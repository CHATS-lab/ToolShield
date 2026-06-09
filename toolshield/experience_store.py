"""Programmatic API for loading and formatting ToolShield safety experiences."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional


# Directory containing bundled experience files shipped with the package.
_EXPERIENCES_DIR = Path(__file__).resolve().parent / "experiences"

# Default model subdirectory when none is specified.
_DEFAULT_MODEL = "claude-sonnet-4.5"


class ExperienceStore:
    """Loads and manages ToolShield safety experience guidelines.

    Each experience file is a JSON object mapping ``"exp.N"`` keys to
    natural-language safety guidelines.  The store aggregates guidelines
    from one or more tool-specific files and can render them as a single
    prompt-ready text block.
    """

    def __init__(self) -> None:
        # tool_name -> {exp_key: guideline_text}
        self._experiences: Dict[str, Dict[str, str]] = {}

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load_file(self, path: str | Path, tool_name: Optional[str] = None) -> None:
        """Load experiences from a JSON file.

        Args:
            path: Path to a JSON experience file.
            tool_name: Human-readable name for the tool.  Defaults to the
                file stem (e.g. ``"terminal-mcp"``).
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Experience file not found: {path}")
        with open(path) as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError(f"Experience file must be a JSON object: {path}")
        if tool_name is None:
            tool_name = path.stem
        self._experiences[tool_name] = data

    def load_bundled(
        self, tool_name: str, model: str = _DEFAULT_MODEL
    ) -> None:
        """Load a bundled experience file by tool name.

        The tool name is matched against files in
        ``toolshield/experiences/<model>/<tool_name>.json``.

        Args:
            tool_name: Name such as ``"terminal-mcp"`` or ``"filesystem-mcp"``.
            model: Model subdirectory (default ``"claude-sonnet-4.5"``).
        """
        path = _EXPERIENCES_DIR / model / f"{tool_name}.json"
        if not path.exists():
            # Try without the .json suffix already present
            path = _EXPERIENCES_DIR / model / tool_name
            if not path.exists():
                available = self.list_bundled(model)
                raise FileNotFoundError(
                    f"No bundled experience for {tool_name!r} (model={model!r}). "
                    f"Available: {', '.join(available)}"
                )
        self.load_file(path, tool_name=tool_name)

    # ------------------------------------------------------------------
    # Querying
    # ------------------------------------------------------------------

    @property
    def tool_names(self) -> List[str]:
        """Return the list of loaded tool names."""
        return list(self._experiences.keys())

    def get_experiences(self, tool_name: str) -> Dict[str, str]:
        """Return the raw experience dict for a specific tool."""
        return dict(self._experiences.get(tool_name, {}))

    def all_experiences(self) -> Dict[str, Dict[str, str]]:
        """Return all loaded experiences keyed by tool name."""
        return {k: dict(v) for k, v in self._experiences.items()}

    # ------------------------------------------------------------------
    # Formatting
    # ------------------------------------------------------------------

    def format_for_prompt(self) -> str:
        """Render all loaded experiences as natural language text.

        Returns a string suitable for injection into an LLM system prompt.
        Each tool's guidelines are grouped under a header.
        """
        if not self._experiences:
            return ""

        sections: list[str] = []
        idx = 0
        for tool_name, exps in self._experiences.items():
            lines: list[str] = [f"## Safety Guidelines for {tool_name}\n"]
            for _key, guideline in sorted(exps.items()):
                idx += 1
                lines.append(f"  {idx}. {guideline}")
            sections.append("\n".join(lines))

        return "\n\n".join(sections)

    # ------------------------------------------------------------------
    # Class helpers
    # ------------------------------------------------------------------

    @staticmethod
    def list_bundled(model: str = _DEFAULT_MODEL) -> List[str]:
        """List available bundled experience file names for a model."""
        model_dir = _EXPERIENCES_DIR / model
        if not model_dir.is_dir():
            return []
        return sorted(p.stem for p in model_dir.glob("*.json"))

    def __len__(self) -> int:
        return sum(len(v) for v in self._experiences.values())

    def __repr__(self) -> str:
        tools = ", ".join(self._experiences.keys()) or "(empty)"
        return f"ExperienceStore(tools=[{tools}], total_guidelines={len(self)})"


def load_experiences(
    tool_names: List[str], model: str = _DEFAULT_MODEL
) -> ExperienceStore:
    """Convenience function: load bundled experiences for multiple tools.

    Args:
        tool_names: List of tool names (e.g. ``["terminal-mcp", "filesystem-mcp"]``).
        model: Model subdirectory for bundled experiences.

    Returns:
        An :class:`ExperienceStore` with all requested tools loaded.
    """
    store = ExperienceStore()
    for name in tool_names:
        store.load_bundled(name, model=model)
    return store
