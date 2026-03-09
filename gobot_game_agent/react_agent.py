from pathlib import Path
import json
import aisuite as ai
import time
import re

from planner import create_plan
from generator import generate_patch
from tools import apply_patch, run_godot_headless, read_file, list_files, get_project_snapshot
from validator import validate_headless_result
from prompts.prompt_template import REACT_TEMPLATE
# agent.py old linear pipeline
# react_agent.py new reasoning agent
PROJECT_PATH = Path(__file__).parent.parent / "playground"

MODEL = "groq:llama-3.3-70b-versatile"
client = ai.Client()

MAX_STEPS = 8

def call_llm(messages):
    resp = client.chat.completions.create(
        model=MODEL,
        messages=messages,
    )
    return resp.choices[0].message.content

def parse_action(text):
    """
    Robustly parse the FIRST Action / Action Input pair from an LLM response.

    Supports:
    - Action: read_file
    - Action:\nread_file
    - Action Input: {"path":"scripts/Player.gd"}
    - Action Input:\n{"path":"scripts/Player.gd"}
    - fenced JSON blocks
    - JSON strings like "scripts/Player.gd"

    Returns:
        (action: str | None, action_input: dict | str | list)
    """
    if not text:
        return None, {}

    lines = text.splitlines()
    action = None
    action_input = {}

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # ---------- Parse Action ----------
        if action is None and line.startswith("Action:"):
            same_line = line[len("Action:"):].strip()

            if same_line:
                action = same_line
            else:
                # Action is on the next non-empty, non-fence line
                j = i + 1
                while j < len(lines):
                    nxt = lines[j].strip()
                    if nxt and not nxt.startswith("```"):
                        action = nxt
                        break
                    j += 1

        # ---------- Parse Action Input ----------
        elif action is not None and line.startswith("Action Input:"):
            same_line = line[len("Action Input:"):].strip()

            # Case 1: input is on same line
            if same_line:
                raw_input = same_line
            else:
                # Case 2: input is on following lines
                collected = []
                j = i + 1
                brace_depth = 0
                started_json = False
                started_string = False

                while j < len(lines):
                    nxt = lines[j].strip()

                    # skip markdown fences
                    if nxt.startswith("```"):
                        j += 1
                        continue

                    # stop if we hit another major section before input starts
                    if not collected and (
                        nxt.startswith("Thought:")
                        or nxt.startswith("Action:")
                        or nxt.startswith("Observation:")
                        or nxt.startswith("FINAL_ANSWER")
                    ):
                        break

                    if not nxt and not collected:
                        j += 1
                        continue

                    collected.append(nxt)

                    # Track JSON object/array
                    if not started_string and (nxt.startswith("{") or nxt.startswith("[")):
                        started_json = True

                    if started_json:
                        brace_depth += nxt.count("{") + nxt.count("[")
                        brace_depth -= nxt.count("}") + nxt.count("]")

                        if brace_depth <= 0:
                            break

                    # Track JSON string input like "scripts/Player.gd"
                    elif not started_json and nxt.startswith('"'):
                        started_string = True
                        if nxt.endswith('"') and len(nxt) >= 2:
                            break

                    # plain scalar fallback: one line only
                    elif not started_json and not started_string:
                        break

                    j += 1

                raw_input = "\n".join(collected).strip()

            # ---------- Decode Action Input ----------
            raw_input = raw_input.strip()

            if not raw_input:
                return action, {}

            # First try strict JSON
            try:
                action_input = json.loads(raw_input)
                return action, action_input
            except Exception:
                pass

            # If wrapped in fences somehow survived, strip and try again
            raw_input_clean = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", raw_input)
            raw_input_clean = re.sub(r"\s*```$", "", raw_input_clean).strip()

            try:
                action_input = json.loads(raw_input_clean)
                return action, action_input
            except Exception:
                pass

            # Last fallback: return plain string
            return action, raw_input_clean

        i += 1

    return action, action_input

def run_react_agent(task: str):

    project_snapshot = get_project_snapshot(PROJECT_PATH)

    prompt = REACT_TEMPLATE.render(task=task, project_snapshot=project_snapshot)

    messages = [
        {"role": "system", "content": prompt}
    ]

    plan = None
    patch = None
    result = None
    for step in range(MAX_STEPS):

        print(f"\n--- STEP {step+1} ---")

        time.sleep(4)
        response = call_llm(messages)
        print(response)

        if "FINAL_ANSWER:" in response:
            final_text = response.split("FINAL_ANSWER:", 1)[1].strip()
            print("\nAgent finished.")
            print("\nFinal answer:")
            print(final_text)
            return

        action, action_input = parse_action(response)

        action, action_input = parse_action(response)
        print("PARSED ACTION:", action)
        print("PARSED INPUT:", action_input)

        if not action:
            observation = "Error: no valid action was parsed from the model response."
            messages.append({"role": "assistant", "content": response})
            messages.append({"role": "user", "content": f"Observation: {observation}"})
            continue

        observation = ""

        if action == "plan":
            print(">>> ENTERED plan BRANCH")
            plan = create_plan(task)
            observation = json.dumps(plan)

        elif action == "generate_patch":
            print(">>> ENTERED generate_patch BRANCH")

            if plan is None:
                print("No plan found. Creating one automatically.")
                plan = create_plan(task)

            patch = generate_patch(task, plan)
            observation = json.dumps(patch)

        elif action == "apply_patch":
            print(">>> ENTERED apply_patch BRANCH")
            written = apply_patch(PROJECT_PATH, patch)
            observation = f"Files written: {written}"
            project_snapshot = get_project_snapshot(PROJECT_PATH)

        elif action == "run_godot":
            print(">>> ENTERED run_godot BRANCH")
            result = run_godot_headless(PROJECT_PATH)
            observation = json.dumps(result)

        elif action == "validate":
            print(">>> ENTERED validate BRANCH")
            if result is None:
                observation = "Error: cannot validate because run_godot has not been executed yet."
            else:
                verdict = validate_headless_result(result)
                observation = json.dumps(verdict)

                if verdict["ok"]:
                    print("\nProject validated successfully.")
                    return
        
        elif action == "list_files":
            print(">>> ENTERED list_files BRANCH")
            if isinstance(action_input, str):
                directory = action_input
            else:
                directory = action_input.get("directory", "")

            if directory in ["project", "project_path", "res://", "."]:
                directory = ""
            
            print(f"Running list_files with directory={directory!r}")
            files = list_files(PROJECT_PATH, directory)
            observation = json.dumps(files[:100])

        elif action == "read_file":
            print(">>> ENTERED read_file BRANCH")

            if isinstance(action_input, str):
                path = action_input
            else:
                path = action_input.get("path")

            if not path:
                observation = "Error: read_file requires a 'path' argument."
            else:
                print(f"Running read_file with path={path!r}")
                content = read_file(PROJECT_PATH, path)
                observation = content[:3000]

        else:
            observation = "Unknown action."

        print("\nObservation:")
        print(observation)

        messages.append({"role": "assistant", "content": response})
        messages.append({"role": "user", "content": f"Observation: {observation}"})

    print("\nAgent stopped (max steps reached)")


def main():
    
    print("=== REACT_AGENT VERSION 2026-03-09 A ===")
    task = input("What do you want Gobot to do?\n> ")

    run_react_agent(task)


if __name__ == "__main__":
    main()