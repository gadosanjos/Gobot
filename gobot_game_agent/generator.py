from __future__ import annotations

import json
import re
from typing import Any, Dict, List
from retriever import retrieve_context

import aisuite as ai
from prompts import prompt_template

client = ai.Client()
MODEL = "groq:llama-3.3-70b-versatile"


# -----------------------------
# Helpers: parsing / extraction
# -----------------------------
def _sanitize_json_text(s: str) -> str:
    """
    Remove problematic control chars that sometimes appear in LLM output
    and normalize fancy quotes. Keeps newlines/tabs only if they are outside
    of JSON strings (we can't perfectly know), so we go conservative: strip
    all ASCII control chars except \n and \t, then normalize some unicode quotes.
    """
    if not s:
        return s

    # Normalize common “smart quotes” into plain quotes
    s = (s.replace("“", '"').replace("”", '"')
           .replace("„", '"').replace("‟", '"')
           .replace("’", "'").replace("‘", "'"))

    # Remove ASCII control chars that break JSON parsing
    # Keep \n and \t because they often appear as formatting outside strings
    s = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", s)
    return s

def _strip_code_fences(text: str) -> str:
    """
    Removes a single outer triple-backtick fence if present.
    Keeps the content intact otherwise.
    """
    text = (text or "").strip()
    if text.startswith("```"):
        # Remove opening fence like ```json
        text = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", text)
        # Remove trailing fence ```
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _extract_first_json_object(text: str) -> str:
    """
    Extracts the first balanced {...} JSON object from the text.
    Useful when the model adds accidental chatter.
    """
    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object found in generator output.")

    depth = 0
    for i in range(start, len(text)):
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]

    raise ValueError("Unclosed JSON object in generator output.")


def _normalize_patch(obj: Any) -> Dict[str, Any]:
    """
    Normalize generator output into the canonical schema:
      {"files":[{"path":"...", "content":"..."}]}

    Supports these input variants:
      - {"files":[{"path":"...", "content":"..."}]}
      - {"files":[{"path":"...", "lines":["...","..."]}]}
    """
    if not isinstance(obj, dict):
        raise ValueError("Patch must be a JSON object.")

    files = obj.get("files")
    if not isinstance(files, list) or not files:
        raise ValueError("Patch must contain non-empty 'files' list.")

    normalized_files: List[Dict[str, str]] = []

    for f in files:
        if not isinstance(f, dict):
            raise ValueError("Each file entry must be an object.")

        path = f.get("path")
        if not isinstance(path, str) or not path.strip():
            raise ValueError("Each file needs a non-empty string 'path'.")

        # Canonical content
        content = f.get("content")

        # If "content" missing, accept "lines": [...]
        if content is None and isinstance(f.get("lines"), list):
            lines = f["lines"]
            # keep only strings
            lines = [ln for ln in lines if isinstance(ln, str)]
            content = "\n".join(lines).rstrip() + "\n"

        if not isinstance(content, str):
            raise ValueError("Each file needs string 'content' (or 'lines' list of strings).")

        normalized_files.append({"path": path.strip(), "content": content})

    return {"files": normalized_files}


def _call_llm(prompt: str, label: str) -> Dict[str, Any]:
    """
    Calls the model, prints raw output, parses JSON, returns normalized patch dict.
    """
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = resp.choices[0].message.content or ""
    print(f"\n--- RAW {label} OUTPUT ---\n", raw, "\n---------------------------\n")

    raw = _strip_code_fences(raw)
    json_text = _extract_first_json_object(raw)
    json_text = _sanitize_json_text(json_text)

    try:
        obj = json.loads(json_text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"{label} returned invalid JSON. Error: {e}\nExtracted:\n{json_text}"
        ) from e

    return _normalize_patch(obj)


# -----------------------------
# Two generators
# -----------------------------

def generate_script_patch(user_request: str, plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Script generator: should output ONLY .gd files.
    Requires prompt_template.SCRIPT_GENERATOR_TEMPLATE to exist.
    """
    docs = retrieve_context(
        query=f"{user_request}\nPLAN: {' '.join(plan.get('steps', []))}\nTARGET: scripts",
        top_k=5,
    )
    prompt = prompt_template.SCRIPT_GENERATOR_TEMPLATE.render(
        task=user_request,
        plan=plan.get("steps", []),
        grounding=getattr(prompt_template, "GODOT_GROUNDING", ""),
        grounding_docs=docs,
    )
    return _call_llm(prompt, "SCRIPT GENERATOR")


def generate_scene_patch(user_request: str, plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Scene generator: should output ONLY .tscn files.
    Requires prompt_template.SCENE_GENERATOR_TEMPLATE to exist.
    """
    docs = retrieve_context(
        query=f"{user_request}\nPLAN: {' '.join(plan.get('steps', []))}\nTARGET: scenes .tscn res:// ext_resource instance",
        top_k=6,
    )
    prompt = prompt_template.SCENE_GENERATOR_TEMPLATE.render(
        task=user_request,
        plan=plan.get("steps", []),
        grounding=getattr(prompt_template, "GODOT_GROUNDING", ""),
        grounding_docs=docs,
    )
    return _call_llm(prompt, "SCENE GENERATOR")


# -----------------------------
# Merge / routing
# -----------------------------

def _should_generate_scenes(user_request: str, plan: Dict[str, Any]) -> bool:
    """
    Small heuristic to avoid always generating scenes.
    - If the request or plan implies scene/node edits, return True.
    - Otherwise, scripts-only.
    """
    text = (user_request or "").lower()

    # If the user is asking to create a game / level / platformer,
    # we almost certainly need scenes.
    keywords = [
        ".tscn", "scene", "level", "platformer", "platform", "floor", "ground",
        "tile", "map", "world", "player scene", "instantiate", "spawn", "node",
        "characterbody2d", "collisionshape2d", "staticbody2d"
    ]
    return any(k in text for k in keywords)


def _merge_patches(*patches: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple normalized patches.
    - Later patches overwrite earlier ones for the same exact path.
    - (Your tools.py now rejects duplicates in a single patch, but merging here is fine.)
    """
    merged: Dict[str, str] = {}

    for p in patches:
        if not p:
            continue
        files = p.get("files", [])
        if not isinstance(files, list):
            continue
        for f in files:
            merged[f["path"]] = f["content"]

    return {"files": [{"path": path, "content": content} for path, content in merged.items()]}


# -----------------------------
# Backwards-compatible entrypoint
# -----------------------------

def generate_patch(user_request: str, plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    TEMP SIMPLIFIED VERSION

    For now we ONLY generate scripts.
    Scene generation is disabled to simplify the agent while we
    implement the ReAct loop.
    """

    return generate_script_patch(user_request, plan)
    
    """
    Backwards-compatible entrypoint used by agent.py :contentReference[oaicite:1]{index=1}

    Default behavior:
    - Always run script generator.
    - Run scene generator only if heuristic says scenes are needed.
    - Merge outputs into one patch.
    
    artifacts = plan.get("artifacts") or {}
    want_scripts = bool(artifacts.get("scripts", True))
    want_scenes  = bool(artifacts.get("scenes", False))

    script_patch = {"files": []}
    scene_patch = {"files": []}

    if want_scripts:
        script_patch = generate_script_patch(user_request, plan)

    if want_scenes:
        scene_patch = generate_scene_patch(user_request, plan)

    return _merge_patches(script_patch, scene_patch)
    """