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

def _normalize_gdscript_indentation(text: str) -> str:
    """
    Convert leading spaces to tabs (Godot default) and prevent mixing.
    Assumes 4 spaces == 1 tab.
    """
    lines = text.splitlines()
    fixed = []

    for line in lines:
        stripped = line.lstrip(" ")
        leading_spaces = len(line) - len(stripped)

        # convert groups of 4 spaces to tabs
        tabs = "\t" * (leading_spaces // 4)
        fixed.append(tabs + stripped)

    return "\n".join(fixed) + "\n"

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
            
                # normalize indentation for GDScript files
        if rel.lower().endswith(".gd"):
            content = _normalize_gdscript_indentation(content)

        target.write_text(content, encoding="utf-8")
        written.append(rel)

    return written

def list_files(project_root: str | Path, directory: str = "") -> list[str]:
    """
    Lists useful project files (relative paths), skipping noisy Godot cache folders.
    """
    root = Path(project_root).resolve()
    target = (root / directory).resolve()

    if not target.exists():
        return [f"Directory not found: {directory}"]

    files = []

    skip_prefixes = [
        ".godot/",
        ".git/",
    ]

    skip_suffixes = [
        ".import",
        ".uid",
        ".cfg",
        ".cache",
        ".bin",
        ".md5",
        ".ctex",
    ]

    for p in target.rglob("*"):
        if not p.is_file():
            continue

        rel = str(p.relative_to(root)).replace("\\", "/")

        if any(rel.startswith(prefix) for prefix in skip_prefixes):
            continue

        if any(rel.endswith(suffix) for suffix in skip_suffixes):
            continue

        files.append(rel)

    return files[:200]


def read_file(project_root: str | Path, path: str) -> str:
    """
    Reads a file from the project so the agent can inspect code.
    """
    root = Path(project_root).resolve()
    target = (root / path).resolve()

    if not target.exists():
        return f"File not found: {path}"

    try:
        return target.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error reading file: {e}"
    
def get_project_snapshot(project_root: str | Path) -> str:
    """
    Returns a compact high-value project snapshot for the agent prompt.
    Focus on useful files/folders, skip Godot cache noise.
    """
    root = Path(project_root).resolve()

    important = {
        "scenes": [],
        "scripts": [],
        "other": []
    }

    for p in root.rglob("*"):
        if not p.is_file():
            continue

        rel = str(p.relative_to(root)).replace("\\", "/")

        if rel.startswith(".godot/") or rel.startswith(".git/"):
            continue

        if rel.startswith("scenes/"):
            important["scenes"].append(rel)
        elif rel.startswith("scripts/"):
            important["scripts"].append(rel)
        else:
            if rel in ["project.godot", "validate_scenes.gd", ".editorconfig", ".gitattributes", ".gitignore"]:
                important["other"].append(rel)

    lines = ["PROJECT SNAPSHOT:"]

    if important["other"]:
        lines.append("other:")
        for f in sorted(important["other"]):
            lines.append(f"  - {f}")

    if important["scenes"]:
        lines.append("scenes:")
        for f in sorted(important["scenes"]):
            lines.append(f"  - {f}")

    if important["scripts"]:
        lines.append("scripts:")
        for f in sorted(important["scripts"]):
            lines.append(f"  - {f}")

    return "\n".join(lines)