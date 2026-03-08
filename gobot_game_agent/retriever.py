from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import List, Tuple, Optional


@dataclass
class Chunk:
    source: str
    text: str


_WORD_RE = re.compile(r"[a-zA-Z0-9_]+")


def _tokenize(text: str) -> List[str]:
    return [t.lower() for t in _WORD_RE.findall(text)]


def _chunk_text(text: str, source: str, max_chars: int = 900) -> List[Chunk]:
    """
    Chunk by paragraphs first; if still too long, fall back to fixed-size slices.
    """
    text = (text or "").strip()
    if not text:
        return []

    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: List[Chunk] = []

    buf = ""
    for p in paras:
        if len(buf) + len(p) + 2 <= max_chars:
            buf = (buf + "\n\n" + p).strip()
        else:
            if buf:
                chunks.append(Chunk(source=source, text=buf))
            # if paragraph itself is too big, slice it
            if len(p) > max_chars:
                for i in range(0, len(p), max_chars):
                    piece = p[i : i + max_chars].strip()
                    if piece:
                        chunks.append(Chunk(source=source, text=piece))
                buf = ""
            else:
                buf = p

    if buf:
        chunks.append(Chunk(source=source, text=buf))

    return chunks


def _score_chunk(query_tokens: List[str], chunk: Chunk) -> int:
    """
    Simple keyword overlap score. (Cheap but works surprisingly well if docs are curated.)
    """
    text_tokens = _tokenize(chunk.text)
    if not text_tokens:
        return 0

    text_set = set(text_tokens)
    score = 0
    for qt in query_tokens:
        if qt in text_set:
            score += 3  # keyword present
    # bonus if chunk has common Godot anchors
    anchors = ["characterbody2d", "move_and_slide", "velocity", "gd_scene", "ext_resource", "sub_resource", "res://"]
    lower = chunk.text.lower()
    score += sum(2 for a in anchors if a in lower)
    return score


def retrieve_context(
    query: str,
    knowledge_dir: Optional[str | Path] = None,
    top_k: int = 5,
) -> str:
    """
    Returns a compact string of the top_k most relevant doc chunks.
    """
    q = (query or "").strip()
    if not q:
        return ""

    base_dir = Path(knowledge_dir) if knowledge_dir else (Path(__file__).parent / "knowledge")
    if not base_dir.exists():
        return ""

    files = []
    for ext in ("*.md", "*.txt"):
        files.extend(base_dir.glob(ext))

    all_chunks: List[Chunk] = []
    for f in files:
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        all_chunks.extend(_chunk_text(text, source=f.name))

    if not all_chunks:
        return ""

    q_tokens = _tokenize(q)
    scored: List[Tuple[int, Chunk]] = []
    for ch in all_chunks:
        s = _score_chunk(q_tokens, ch)
        if s > 0:
            scored.append((s, ch))

    if not scored:
        return ""

    scored.sort(key=lambda x: x[0], reverse=True)
    chosen = [ch for _, ch in scored[:top_k]]

    # Format as a “reference pack”
    out_lines = ["REFERENCE DOC SNIPPETS (use as ground truth):"]
    for i, ch in enumerate(chosen, 1):
        out_lines.append(f"\n[SNIPPET {i} — {ch.source}]")
        out_lines.append(ch.text.strip())

    return "\n".join(out_lines).strip()