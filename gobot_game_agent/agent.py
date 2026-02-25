from pathlib import Path
from tools import run_godot_headless, apply_patch
from validator import validate_headless_result
from planner import create_plan
from generator import generate_patch

# This points from gobot_game_agent -> playground (sibling folder)
PROJECT_PATH = Path(__file__).parent.parent / "playground"

def main():
    user_request = input("What do you want the agent to do?\n> ")

    print("\n--- PLANNER ---")
    plan = create_plan(user_request)
    print(plan)

    print("\n--- GENERATOR ---")
    patch = generate_patch(user_request, plan)
    print(f"Patch wants to write {len(patch['files'])} file(s).")

    print("\n--- EXECUTOR (write files) ---")
    written = apply_patch(PROJECT_PATH, patch)
    for p in written:
        print("WROTE:", p)

    print("\n--- EXECUTOR (godot headless) ---")
    result = run_godot_headless(PROJECT_PATH)

    print("\n--- VALIDATOR ---")
    verdict = validate_headless_result(result)
    print("PASS ✅" if verdict["ok"] else "FAIL ❌")
    if not verdict["ok"]:
        print("Reason:", verdict["reason"])

# Entry point
if __name__ == "__main__":
    main()
