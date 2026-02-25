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