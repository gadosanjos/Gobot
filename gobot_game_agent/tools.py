from __future__ import annotations
import subprocess
from pathlib import Path

GODOT_EXE = r"C:\Users\dosan\Desktop\GradLevel\2-Spring 2026\CS264\agenticAI\gobot\Godot_v4.6.1-stable_win64\Godot_v4.6.1-stable_win64_console.exe"

def run_godot_headless(project_dir: str | Path) -> dict:
    """
    Runs: Godot --headless --path <project_dir> --quit
    Returns stdout/stderr/returncode so the agent can validate and iterate.
    """
    project_dir = str(Path(project_dir).resolve())

    cmd = [GODOT_EXE, "--headless", "--path", project_dir, "--quit"]

    p = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "cmd": " ".join(cmd),
        "returncode": p.returncode,
        "stdout": p.stdout,
        "stderr": p.stderr,
    }