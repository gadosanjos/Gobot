from __future__ import annotations
import subprocess
from pathlib import Path

GODOT_EXE = str(Path(__file__).parent.parent / "Godot_v4.6.1-stable_win64\Godot_v4.6.1-stable_win64_console.exe")

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

from pathlib import Path

def apply_patch(project_root: str | Path, patch: dict) -> list[str]:
    """
    Writes patch["files"] into the Godot project folder safely.
    Returns list of written file paths.
    """
    project_root = Path(project_root).resolve()
    written: list[str] = []

    files = patch.get("files", [])
    if not isinstance(files, list):
        raise ValueError("patch['files'] must be a list")

    for f in files:
        rel = f["path"].replace("\\", "/").strip()

        # Safety: no absolute paths, no parent traversal
        # Normalize Godot resource paths to project-relative paths
        if rel.startswith("res://"):
            rel = rel[len("res://"):]
        if rel.startswith("/") or rel.startswith("~") or ":" in rel:
            raise ValueError(f"Unsafe path (absolute): {rel}")
        if ".." in Path(rel).parts:
            raise ValueError(f"Unsafe path (.. traversal): {rel}")
        # Don’t allow the agent to edit project.godot by default
        if rel == "project.godot":
            raise ValueError("Refusing to overwrite project.godot. Ask explicitly if you really want this.")
        target = (project_root / rel).resolve()

        # Safety: enforce staying inside project_root
        if project_root not in target.parents and target != project_root:
            raise ValueError(f"Unsafe path (outside project): {rel}")

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f["content"], encoding="utf-8")
        written.append(rel)

    return written