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

