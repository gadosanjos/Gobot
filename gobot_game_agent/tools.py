from __future__ import annotations
import subprocess
from pathlib import Path
from validator import _looks_like_valid_tscn

GODOT_EXE = str(
    Path(__file__).parent.parent 
    / "Godot_v4.6.1-stable_win64\Godot_v4.6.1-stable_win64_console.exe"
)

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

def run_godot_validate_scenes(project_dir: str | Path) -> dict:
    project_dir = str(Path(project_dir).resolve())
    cmd = [GODOT_EXE, "--headless", "--path", project_dir, "--script", "res://validate_scenes.gd"]
    p = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "cmd": " ".join(cmd),
        "returncode": p.returncode,
        "stdout": p.stdout,
        "stderr": p.stderr,
    }

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
    
    # NEW: reject duplicate file targets in a single patch (prevents overwrites)
    seen: set[str] = set()

    for f in files:
        if not isinstance(f, dict):
            raise ValueError("Each file entry must be an object")

        if "path" not in f or "content" not in f:
            raise ValueError("Each file entry must include 'path' and 'content'")

        rel = str(f["path"]).replace("\\", "/").strip()

        # Normalize Godot resource paths to project-relative paths
        if rel.startswith("res://"):
            rel = rel[len("res://") :]

        # NEW: reject duplicates after normalization
        if rel in seen:
            raise ValueError(f"Duplicate file in patch: {rel}")
        seen.add(rel)

        # Safety: no absolute paths, no parent traversal
        if rel.startswith("/") or rel.startswith("~") or ":" in rel:
            raise ValueError(f"Unsafe path (absolute): {rel}")
        if ".." in Path(rel).parts:
            raise ValueError(f"Unsafe path (.. traversal): {rel}")

        # Safety: block project.godot edits by default
        if rel == "project.godot":
            raise ValueError(
                "Refusing to overwrite project.godot. Ask explicitly if you really want this."
            )

        target = (project_root / rel).resolve()

        # Safety: enforce staying inside project_root
        if project_root not in target.parents and target != project_root:
            raise ValueError(f"Unsafe path (outside project): {rel}")

        target.parent.mkdir(parents=True, exist_ok=True)

        content = f["content"]
        if not isinstance(content, str):
            content = str(content)

        # ✅ NEW: reject invalid .tscn before writing
        if rel.endswith(".tscn"):
            if not _looks_like_valid_tscn(content):
                raise ValueError(
                    f"Invalid .tscn content detected for {rel}. "
                    "Scene must start with [gd_scene] and be valid Godot scene format."
                )
            
        target.write_text(content, encoding="utf-8")
        written.append(rel)

    return written
