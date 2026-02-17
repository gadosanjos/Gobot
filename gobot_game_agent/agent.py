from pathlib import Path
from tools import run_godot_headless

# This points from gobot_game_agent -> playground (sibling folder)
PROJECT_PATH = Path(__file__).parent.parent / "playground"

def main():
    result = run_godot_headless(PROJECT_PATH)

    print("=== COMMAND ===")
    print(result["cmd"])
    print("\n=== RETURN CODE ===")
    print(result["returncode"])
    print("\n=== STDOUT ===")
    print(result["stdout"].strip())
    print("\n=== STDERR ===")
    print(result["stderr"].strip())

# Entry point
if __name__ == "__main__":
    main()
