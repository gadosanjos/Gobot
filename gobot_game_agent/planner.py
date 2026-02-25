import json
import aisuite as ai
from prompts import prompt_template

client = ai.Client()

MODEL = "groq:llama-3.3-70b-versatile"

def create_plan(user_request: str) -> dict:
    """
    Calls the LLM to create a structured plan.
    """

    prompt = prompt_template.PLANNER_TEMPLATE.render(task=user_request)

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )

    content = response.choices[0].message.content

    try:
        return json.loads(content)
    except Exception:
        return {"steps": [content.strip()]}