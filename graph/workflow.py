from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
from anthropic import Anthropic
from langfuse import Langfuse
from skills import SkillRegistry
from router.agent import route
from memory.manager import MemoryManager
from config.settings import settings

client = Anthropic(api_key=settings.anthropic_api_key)
langfuse = Langfuse(
    host=settings.langfuse_host,
    public_key=settings.langfuse_public_key,
    secret_key=settings.langfuse_secret_key,
)
registry = SkillRegistry()
memory_manager = MemoryManager()


class State(TypedDict):
    messages: Annotated[list, add_messages]
    session_id: str
    skill_name: str
    tools: list
    context: str


async def memory_node(state: State) -> dict:
    user_input = state["messages"][-1].content
    ctx = await memory_manager.get_context(state["session_id"], user_input)
    return {"context": ctx}


def router_node(state: State) -> dict:
    user_input = state["messages"][-1].content
    skill_name = route(user_input, state["session_id"])
    return {"skill_name": skill_name}


def load_skill_node(state: State) -> dict:
    tools = registry.load_skill(state["skill_name"])
    return {"tools": tools}


def execute_node(state: State) -> dict:
    user_input = state["messages"][-1].content
    skill_name = state["skill_name"]
    context = state.get("context", "")
    tools = state["tools"]

    system = f"你是 TaskPilot 助手，当前使用 {skill_name} Skill。"
    if context:
        system += f"\n\n{context}"

    # 构造工具描述让 LLM 感知可用工具
    tool_descriptions = "\n".join(
        f"- {t['name']}: {t['description']}" for t in tools
    )
    if tool_descriptions:
        system += f"\n\n可用工具：\n{tool_descriptions}"

    trace = langfuse.trace(name="execute", session_id=state["session_id"], input=user_input)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": user_input}],
    )

    answer = response.content[0].text
    trace.update(output=answer)

    # 异步写长期记忆（fire-and-forget 简化版）
    import asyncio
    asyncio.create_task(
        memory_manager.long.save(state["session_id"], f"用户：{user_input}\n助手：{answer}")
    )
    memory_manager.short.add(state["session_id"], "user", user_input)
    memory_manager.short.add(state["session_id"], "assistant", answer)

    from langchain_core.messages import AIMessage
    return {"messages": [AIMessage(content=answer)]}


def build_graph() -> StateGraph:
    builder = StateGraph(State)
    builder.add_node("memory", memory_node)
    builder.add_node("router", router_node)
    builder.add_node("load_skill", load_skill_node)
    builder.add_node("execute", execute_node)

    builder.set_entry_point("memory")
    builder.add_edge("memory", "router")
    builder.add_edge("router", "load_skill")
    builder.add_edge("load_skill", "execute")
    builder.add_edge("execute", END)

    checkpointer = MemorySaver()
    return builder.compile(checkpointer=checkpointer)


app = build_graph()
