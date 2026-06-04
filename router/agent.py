import json
from anthropic import Anthropic
from langfuse import Langfuse
from skills import SkillRegistry
from config.settings import settings

client = Anthropic(api_key=settings.anthropic_api_key)
langfuse = Langfuse(
    host=settings.langfuse_host,
    public_key=settings.langfuse_public_key,
    secret_key=settings.langfuse_secret_key,
)
registry = SkillRegistry()


def route(user_input: str, session_id: str = "default") -> str:
    skills = registry.list_skills()
    skill_list = "\n".join(f"- {s['name']}: {s['description']}" for s in skills)

    trace = langfuse.trace(name="router", session_id=session_id, input=user_input)
    span = trace.span(name="llm_call")

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=64,
        system=f"""你是任务路由器，根据用户输入选择最合适的 Skill。
可用 Skill：
{skill_list}

只输出 JSON：{{"skill": "<skill_name>"}}，不要其他内容。""",
        messages=[{"role": "user", "content": user_input}],
    )

    text = response.content[0].text.strip()
    result = json.loads(text)
    skill_name = result["skill"]

    span.end(output=skill_name)
    trace.update(output=skill_name)

    return skill_name
