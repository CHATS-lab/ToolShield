#!/usr/bin/env python3
"""
MCP Server Scanner - Scan local ports to auto-discover MCP servers
Usage: python mcp_scanner.py [start_port] [end_port]
Default scan range: 8000-10000
"""

import asyncio
import aiohttp
import json
import sys
import time
import socket


INIT_PAYLOAD = json.dumps({
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "clientInfo": {"name": "mcp-scanner", "version": "1.0"},
        "capabilities": {}
    }
})

SSE_PATHS = ["/sse", "/mcp/sse", "/mcp"]


def is_port_open(port, timeout=0.5):
    """Check if a port is open (supports both IPv4 and IPv6)"""
    for family, addr in [(socket.AF_INET, "127.0.0.1"), (socket.AF_INET6, "::1")]:
        try:
            s = socket.socket(family, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect((addr, port))
            s.close()
            return True
        except (ConnectionRefusedError, OSError, socket.timeout):
            try:
                s.close()
            except OSError:
                pass
    return False


async def read_sse_events(resp, max_events=10, timeout=3):
    """Parse events from an SSE response stream"""
    events = []
    cur_event = {}
    try:
        deadline = asyncio.get_event_loop().time() + timeout
        async for raw_line in resp.content:
            if asyncio.get_event_loop().time() > deadline:
                break
            line = raw_line.decode("utf-8", errors="ignore").rstrip("\n\r")
            if line.startswith("event:"):
                cur_event["event"] = line[len("event:"):].strip()
            elif line.startswith("data:"):
                cur_event["data"] = line[len("data:"):].strip()
            elif line == "" and cur_event:
                events.append(cur_event)
                cur_event = {}
                if len(events) >= max_events:
                    break
    except (asyncio.TimeoutError, aiohttp.ClientError):
        pass
    if cur_event:
        events.append(cur_event)
    return events


async def try_mcp_handshake(session, port, path, timeout=5):
    """Attempt a full MCP handshake on a given port and path"""
    base = f"http://127.0.0.1:{port}"
    sse_url = f"{base}{path}"

    try:
        # Step 1: GET /sse to establish SSE connection and retrieve endpoint
        async with session.get(sse_url, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
            if resp.status != 200:
                return None

            ct = resp.headers.get("Content-Type", "")
            if "text/event-stream" not in ct:
                return None

            # Read the first event to get the endpoint
            events = await read_sse_events(resp, max_events=1, timeout=2)

        endpoint = None
        for ev in events:
            d = ev.get("data", "")
            if d.startswith("/"):
                endpoint = d
                break

        if not endpoint:
            return None

        # Step 2: Open a new SSE connection and send initialize
        async with session.get(sse_url, timeout=aiohttp.ClientTimeout(total=timeout)) as resp2:
            if resp2.status != 200:
                return None

            # Read the new session's endpoint
            events2 = await read_sse_events(resp2, max_events=1, timeout=2)
            endpoint2 = None
            for ev in events2:
                d = ev.get("data", "")
                if d.startswith("/"):
                    endpoint2 = d
                    break

            if not endpoint2:
                return None

            post_url = f"{base}{endpoint2}"

            # Fire POST initialize (non-blocking)
            asyncio.ensure_future(_post(session, post_url, timeout))

            # Read the initialize response from the SSE stream
            events3 = await read_sse_events(resp2, max_events=5, timeout=timeout)

            for ev in events3:
                d = ev.get("data", "")
                if d.startswith("{"):
                    try:
                        parsed = json.loads(d)
                        if "result" in parsed and "serverInfo" in parsed["result"]:
                            return parsed["result"]["serverInfo"]
                    except json.JSONDecodeError:
                        pass

    except (aiohttp.ClientError, asyncio.TimeoutError, OSError, ConnectionError):
        return None

    return None


async def _post(session, url, timeout=5):
    """Send POST initialize request"""
    try:
        async with session.post(
            url,
            data=INIT_PAYLOAD,
            headers={"Content-Type": "application/json"},
            timeout=aiohttp.ClientTimeout(total=timeout)
        ) as r:
            await r.text()
    except Exception:
        pass


async def scan_port(sem, session, port, verbose=False):
    """Scan a single port for MCP servers"""
    async with sem:
        for path in SSE_PATHS:
            if verbose:
                print(f"  Probing port {port}{path}...")
            info = await try_mcp_handshake(session, port, path)
            if info:
                return {
                    "port": port,
                    "path": path,
                    "name": info.get("name", "unknown"),
                    "version": info.get("version", "unknown"),
                    "url": f"http://localhost:{port}{path}"
                }
    return None


async def main(start_port, end_port, verbose=False):
    print(f"🔍 Scanning localhost:{start_port}-{end_port} for MCP servers...\n")
    t0 = time.time()

    # Step 1: Fast port scan using sockets (supports IPv4/IPv6)
    loop = asyncio.get_event_loop()
    open_ports = []
    tasks = [loop.run_in_executor(None, is_port_open, p) for p in range(start_port, end_port + 1)]
    results = await asyncio.gather(*tasks)
    for i, is_open in enumerate(results):
        if is_open:
            open_ports.append(start_port + i)

    print(f"📡 Found {len(open_ports)} open port(s): {open_ports}\n")

    if not open_ports:
        print("❌ No open ports found")
        return []

    # Step 2: Probe open ports for MCP servers
    sem = asyncio.Semaphore(10)
    connector = aiohttp.TCPConnector(limit=20, force_close=True)

    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [scan_port(sem, session, p, verbose) for p in open_ports]
        results = await asyncio.gather(*tasks)

    found = [r for r in results if r]
    elapsed = time.time() - t0

    if found:
        print(f"✅ Found {len(found)} MCP server(s) in {elapsed:.1f}s:\n")
        print(f"  {'Port':<8} {'Name':<25} {'Version':<15} {'URL'}")
        print(f"  {'-'*75}")
        for s in sorted(found, key=lambda x: x["port"]):
            print(f"  {s['port']:<8} {s['name']:<25} {s['version']:<15} {s['url']}")
    else:
        print(f"❌ No MCP servers found among {len(open_ports)} open ports in {elapsed:.1f}s")

    print()
    return found


if __name__ == "__main__":
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    start = int(args[0]) if len(args) > 0 else 8000
    end = int(args[1]) if len(args) > 1 else 10000
    asyncio.run(main(start, end, verbose))