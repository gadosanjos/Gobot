from __future__ import annotations

import json
import re
from typing import Any, Dict, List

import aisuite as ai
from prompts import prompt_template

client = ai.Client()
MODEL = "groq:llama-3.1-8b-instant"


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


def generate_patch(user_request: str, plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generator (LLM call): returns normalized patch:
      {"files":[{"path":"...","content":"..."}]}
    """
    prompt = prompt_template.GENERATOR_TEMPLATE.render(
        task=user_request,
        plan=plan.get("steps", []),
    )

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = resp.choices[0].message.content or ""
    print("\n--- RAW GENERATOR OUTPUT ---\n", raw, "\n---------------------------\n")

    raw = _strip_code_fences(raw)
    json_text = _extract_first_json_object(raw)

    try:
        obj = json.loads(json_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Generator returned invalid JSON. Error: {e}\nExtracted:\n{json_text}") from e

    return _normalize_patch(obj)