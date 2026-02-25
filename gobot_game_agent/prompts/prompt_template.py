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
    - Target: 2D platformer unless explicitly stated otherwise

    REQUIREMENTS:
    - Return ONLY valid JSON (no markdown, no backticks, no commentary).
    - JSON schema MUST be exactly:

    {{
      "artifacts": {{
        "scripts": true,
        "scenes": true,
        "project_settings": false
      }},
      "steps": ["...", "..."]
    }}

    - 3 to 8 steps.
    - Each step: short imperative (max ~10 words).
    - Use Godot 4 node names (CharacterBody2D, Node2D, CollisionShape2D).
    - Do NOT include code.
    - Do NOT mention tools/CLI/python.
    - If the request implies new nodes / levels / a playable game, set artifacts.scenes = true.
    - If the request implies movement/behavior, set artifacts.scripts = true.
    - Only set artifacts.project_settings = true if the user explicitly asked to change project settings.

    OUTPUT FORMAT (STRICT): Return ONLY valid JSON.
    """),
)

SCRIPT_GENERATOR_TEMPLATE = PromptTemplate(
    name="Gobot Script Generator Patch",
    tags=["gobot", "generator", "godot", "patch", "json", "scripts"],
    template=dedent("""
    You are the SCRIPT GENERATOR for a Godot 4 automation agent.

    JOB:
    Create or update ONLY GDScript files (.gd) as a patch.

    USER REQUEST:
    {task}

    PLAN (context only):
    {plan}

    CONSTRAINTS:
    - Engine: Godot 4.x
    - Language: GDScript only
    - Output ONLY .gd files. (Do NOT output .tscn, project.godot, .import, etc.)
    - Prefer minimal implementation over completeness.
    - Do NOT invent APIs.
    - Do NOT include commentary or markdown.

    OUTPUT FORMAT (STRICT):
    Return ONLY valid JSON with EXACT schema:

    {{
      "files": [
        {{
          "path": "relative/path.gd",
          "lines": ["line1", "line2", "..."]
        }}
      ]
    }}

    RULES:
    - paths must be relative to project root, forward slashes, NO res://
    - EXACTLY one entry per file path (no duplicates).
    - For edits, output the FULL file contents in "lines".
    - Do NOT touch project.godot.
    - If creating a player script, ALWAYS write it to scripts/Player.gd (not Player.gd).
    - Include 'func' for all functions (e.g., 'func _physics_process(delta):').

    GODOT 4 MOVEMENT PREFERENCE:
    - Top-down movement:
      var input_dir = Input.get_vector("ui_left","ui_right","ui_up","ui_down")
    - CharacterBody2D usage:
      velocity = input_dir * SPEED
      move_and_slide()

    OUTPUT: JSON only.
    """),
)

SCENE_GENERATOR_TEMPLATE = PromptTemplate(
    name="Gobot Scene Generator Patch",
    tags=["gobot", "generator", "godot", "patch", "json", "scenes"],
    template=dedent("""
    You are the SCENE GENERATOR for a Godot 4 automation agent.

    JOB:
    Create or update ONLY Godot scene files (.tscn) as a patch.

    USER REQUEST:
    {task}

    PLAN (context only):
    {plan}

    CONSTRAINTS:
    - Engine: Godot 4.x
    - ASCII ONLY (no smart quotes).
    - Output ONLY .tscn files (no .gd, no project.godot).
    - Return ONLY valid JSON (no markdown).

    OUTPUT FORMAT (STRICT):
    Return ONLY valid JSON with EXACT schema:
    {{
    "files": [
        {{
        "path": "scenes/Level.tscn",
        "lines": ["line1", "line2", "..."]
        }}
    ]
    }}

    RULES (MUST FOLLOW):
    - paths in JSON are project-relative (like scenes/Level.tscn). NO "res://"
    - BUT inside .tscn text, ALL resource paths MUST use res://
    - EXACTLY one entry per file path (no duplicates)
    - Output FULL .tscn contents in "lines"
    - .tscn MUST start with: [gd_scene load_steps=... format=3]

    YOU MUST GENERATE A MINIMAL PLATFORMER SETUP:
    Create TWO scenes:
    1) scenes/Player.tscn:
    - root CharacterBody2D named Player
    - CollisionShape2D with RectangleShape2D sub_resource
    - script ext_resource points to res://scripts/Player.gd
    2) scenes/Level.tscn:
    - root Node2D named Level
    - instanced Player scene using ext_resource type="PackedScene"
    - StaticBody2D Floor with CollisionShape2D RectangleShape2D

    GOLDEN EXAMPLES (follow this structure exactly):

    --- scenes/Player.tscn ---
    [gd_scene load_steps=3 format=3]

    [ext_resource type="Script" path="res://scripts/Player.gd" id="1"]

    [sub_resource type="RectangleShape2D" id="1"]
    size = Vector2(16, 32)

    [node name="Player" type="CharacterBody2D"]
    script = ExtResource("1")

    [node name="CollisionShape2D" type="CollisionShape2D" parent="."]
    shape = SubResource("1")

    --- scenes/Level.tscn ---
    [gd_scene load_steps=3 format=3]

    [ext_resource type="PackedScene" path="res://scenes/Player.tscn" id="1"]

    [sub_resource type="RectangleShape2D" id="1"]
    size = Vector2(320, 32)

    [node name="Level" type="Node2D"]

    [node name="Player" parent="." instance=ExtResource("1")]
    position = Vector2(0, 0)

    [node name="Floor" type="StaticBody2D" parent="."]
    position = Vector2(0, 280)

    [node name="CollisionShape2D" type="CollisionShape2D" parent="Floor"]
    shape = SubResource("1")

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

