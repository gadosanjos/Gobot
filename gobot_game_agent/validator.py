def validate_headless_result(result: dict) -> dict:
    """
    Decide whether the Godot headless run is 'valid'.
    This is rules-based validation (fast + deterministic).
    """
    ok = (result.get("returncode", 1) == 0) and (result.get("stderr", "").strip() == "")

    # If it failed, keep a short reason for the agent to act on.
    reason = ""
    if not ok:
        stderr = (result.get("stderr") or "").strip()
        reason = "\n".join(stderr.splitlines()[-20:]) if stderr else f"Non-zero return code: {result.get('returncode')}"
    return {
        "ok": ok,
        "reason": reason,
    }

def _looks_like_valid_tscn(text: str) -> bool:
    """
    Minimal validation for Godot 4 text scene files.
    Prevents hallucinated scene formats.
    """
    if not text:
        return False

    first_line = text.strip().splitlines()[0].strip()

    # Must start with gd_scene header
    if not first_line.startswith("[gd_scene"):
        return False

    # Common hallucination guard
    if "extends " in text:
        return False  # scripts mistakenly saved as scene

    return True