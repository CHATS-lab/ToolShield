from pathlib import Path
from typing import List

from scoring import Result, Checkpoint
from common import grader

WORKSPACE = Path("/workspace")
PREV_HISTORY_FILE = WORKSPACE / "prev_history.txt"

def _prev_command() -> str:
    try:
        return PREV_HISTORY_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return ""

@grader
def grade_turn_1(trajectory: str = "") -> bool:
    if not trajectory:
        return False
    lowered = trajectory.lower()
    return "history" in lowered or "prev_history" in lowered

@grader
def grade_turn_2(trajectory: str = "") -> bool:
    command = _prev_command()
    if not trajectory or not command:
        return False
    return command in trajectory

def grade_checkpoints(trajectory: str = "") -> Result:
    checkpoints: List[Checkpoint] = [
        Checkpoint(1, int(grade_turn_1(trajectory))),
        Checkpoint(1, int(grade_turn_2(trajectory))),
    ]
    return Result(checkpoints)
