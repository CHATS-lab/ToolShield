"""ToolShield — Training-free defense for multi-turn safety risks in tool-using AI agents."""

from importlib.metadata import PackageNotFoundError, version as _pkg_version

try:
    # Single source of truth: ``pyproject.toml`` drives the version,
    # exposed via the installed package metadata. Avoids the historical
    # desync between pyproject.toml, ``__version__``, and the published
    # wheel (see issue #4).
    __version__ = _pkg_version("toolshield")
except PackageNotFoundError:
    # Editable / from-source install without installed metadata.
    __version__ = "0.0.0+unknown"

from toolshield.experience_store import ExperienceStore, load_experiences
from toolshield.inspector import MCPSSEInspector, MCPStreamableHTTPInspector

# Backwards compatibility
MCPInspector = MCPSSEInspector

__all__ = [
    "ExperienceStore",
    "MCPInspector",
    "MCPSSEInspector",
    "MCPStreamableHTTPInspector",
    "__version__",
    "load_experiences",
]
