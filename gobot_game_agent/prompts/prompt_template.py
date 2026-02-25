from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
import re
import textwrap

@dataclass
# PromptTemplate = a reusable prompt “object” with placeholders like {role}, {task}, etc.
class PromptTemplate:
    name: str
    template: str
    notes: str = ""
    tags: List[str] = field(default_factory=list)

    def render(self, **kwargs) -> str:
        return self.template.format(**kwargs)

# dedent = cleans indentation so your templates look nice
def dedent(s: str) -> str:
    return textwrap.dedent(s).strip()

# extract_with_regex = optional helper for “answer engineering” (pull FinalAnswer: etc.)
def extract_with_regex(text: str, pattern: str, group: int = 1) -> Optional[str]:
    """Tiny 'answer engineering' helper: extract a stable field from a messy response."""
    m = re.search(pattern, text, flags=re.DOTALL)
    return m.group(group).strip() if m else None

# Reusable “skeleton prompts”

# BASE_SKELETON = minimal universal base, no ICL, no do-nots, minimal checks.
# Examples are missing explicitly. 
# That was intentional because: Not all prompts use ICL, minimal universal base.
# Checks: Forces internal evaluation, Improves reliability, Acts like lightweight self-critique
BASE_SKELETON = PromptTemplate(
    name="Base Skeleton",
    tags=["general"],
    template=dedent("""
    ROLE:
    {role}

    DIRECTIVE:
    {directive}

    CONTEXT:
    {context}

    OUTPUT FORMAT:
    {format}

    QUALITY BAR / CHECKS:
    {checks} 
    """),
)

BASE_SKELETON_ICL = PromptTemplate(
    name="Base Skeleton (Full Components)",
    tags=["general"],
    template=dedent("""
    ROLE:
    {role}

    DIRECTIVE:
    {directive}

    CONTEXT:
    {context}

    EXAMPLES (optional, for ICL):
    {examples}

    OUTPUT FORMAT:
    {format}

    QUALITY BAR / CHECKS:
    {checks}
    """),
)

BASE_SKELETON_BETTER = PromptTemplate(
    name="Base Skeleton (Engineer)",
    tags=["general"],
    template=dedent("""
    ROLE:
    {role}

    DIRECTIVE:
    {directive}

    CONTEXT / GIVEN:
    {context}

    EXAMPLES (optional):
    {examples}
                    
    OUTPUT FORMAT (strict):
    {format}

    NON-GOALS / DO-NOT:
    {donts}

    QUALITY BAR / CHECKS:
    {checks}
    """),
)

CODEGEN_SKELETON = PromptTemplate(
    name="Codegen Skeleton",
    tags=["codegen"],
    template=dedent("""
    You are a careful software engineer.

    Task:
    {task}

    Constraints:
    - Language: {language}
    - Must satisfy: {requirements}
    - Edge cases: {edge_cases}

    Output format (strict):
    {output_format}

    If uncertain, state assumptions explicitly (do not invent APIs).
    """),
)

CODEGEN_SKELETON_BETTER = PromptTemplate(
    name="Codegen Skeleton (Engineer)",
    tags=["codegen"],
    template=dedent("""
    You are a careful software engineer.

    Task:
    {task}

    GIVEN (inputs/interfaces):
    {given}

    Constraints:
    {constraints}

    Edge cases:
    {edge_cases}

    Output format (STRICT):
    {output_format}

    Non-goals / do-not:
    {donts}

    Acceptance tests (must pass):
    {tests}

    If critical info is missing, ask up to 3 questions; otherwise state assumptions explicitly.
    """),
)

PLANNER_TEMPLATE = PromptTemplate(
    name="Gobot Planner",
    tags=["gobot", "planner", "godot", "json"],
    template=dedent("""
    You are the PLANNER for a Godot 4 game-building automation agent.

    USER REQUEST:
    {task}

    PROJECT CONTEXT:
    - Engine: Godot 4.
    - Language: GDScript                
    - Target: 2D platoformer game project unless explicitly stated otherwise
    - Existing scene structure may already exist
    - Goal: produce a small actionable plan that can be executed by a generator + tools

    REQUIREMENTS:
    - Return ONLY valid JSON (no markdown, no backticks, no commentary).
    - JSON schema MUST be exactly:
    {{
        "steps": ["...", "..."]
    }}
    - 3 to 8 steps.
    - Each step: short imperative (max ~10 words).
    - Use Godot 4 node names (CharacterBody2D, Node2D, CollisionShape2D).
    - Do NOT include implementation details like exact code.
    - Do NOT mention tools, CLI, or python internals.

    PLANNING STYLE:
    - Prefer minimal viable solution.
    - If the request is ambiguous, make 1–2 reasonable assumptions
    and include them as steps like: "Assume 2D top-down movement".

    OUTPUT FORMAT (STRICT — MUST FOLLOW EXACTLY): Return ONLY valid JSON.
    """),
)


GENERATOR_TEMPLATE = PromptTemplate(
    name="Gobot Generator Patch",
    tags=["gobot", "generator", "godot", "patch", "json"],
    template=dedent("""
    You are the GENERATOR for a Godot 4 automation agent.

    JOB:
    Produce project files/edits as a patch.

    USER REQUEST:
    {task}

    PLAN (context only):
    {plan}

    CONSTRAINTS:
    - Engine: Godot 4.x
    - Target: 2D platoformer game project unless explicitly stated otherwise
    - Use ONLY valid Godot 4 concepts and file formats.
    - Prefer minimal implementation over completeness.
    - Do NOT invent APIs.
    - Do NOT add features not requested.
    - Do NOT include commentary.

    OUTPUT FORMAT (STRICT):
    Return ONLY valid JSON with EXACT schema:

    {{
    "files": [
        {{
        "path": "relative/path.ext",
        "lines": ["line1", "line2", "..."]
        }}
    ]
    }}

    RULES:
    - paths must be relative to project root, use forward slashes.
    - Each file uses "lines" only (no multiline "content" strings).
    - No markdown fences, no explanations.
    - If you must modify an existing file, output the full new file contents in "lines".

    GODOT-SPECIFIC RULES:
    - .gd files must be valid GDScript.
    - .tscn files must be valid Godot text scene format (NOT JSON).
    - Prefer CharacterBody2D for player movement.
    - For movement, use:
    Input.get_vector("ui_left","ui_right","ui_up","ui_down") and move_and_slide()

    SAFETY / VALIDATION FRIENDLY:
    - Keep changes minimal to reduce runtime errors.
    - Avoid touching project.godot unless explicitly requested.

    OUTPUT: JSON only.
    """),
)

def main():
    # Example usage
    prompt = PromptTemplate(
        name="Example Prompt",
        template=dedent("""
            You are a helpful assistant.
            Your task is: {task}
            Please provide a detailed answer.
        """),
        notes="This is an example prompt template.",
        tags=["example", "test"]
    )

    rendered = prompt.render(task="Explain the theory of relativity.")
    print("=== RENDERED PROMPT ===")
    print(rendered)

if __name__ == "__main__":
    main()

