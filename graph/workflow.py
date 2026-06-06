from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from anthropic import Anthropic
from langfuse import Langfuse
from langchain_core.messages import AIMessage

from skills import SkillRegistry
from skills.registry_impl import get_impl
import skills.impls  # noqa: F401 — 触发所有 @register 装饰器
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

MAX_ITERATIONS = 5


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


def _call_tool(tool_name: str, tool_input: dict, span) -> str:
    """执行工具，失败重试一次，结果记录为 Langfuse 事件"""
    fn = get_impl(tool_name)
    if fn is None:
        return f"ERROR: 工具 {tool_name} 未实现"

    for attempt in range(2):  # 最多 2 次（1 次 + 重试 1 次）
        try:
            result = fn(**tool_input)
            span.event(name=tool_name, input=tool_input, output=result)
            return result
        except Exception as e:
            if attempt == 0:
                span.event(name=f"{tool_name}_retry", input=tool_input, output=str(e))
                continue
            return f"ERROR: {tool_name} 执行失败：{e}"


def execute_node(state: State) -> dict:
    user_input = state["messages"][-1].content
    skill_name = state["skill_name"]
    context = state.get("context", "")
    tools = state["tools"]  # 已是 Anthropic input_schema 格式

    system = f"你是 TaskPilot 助手，当前使用 {skill_name} Skill。"
    if context:
        system += f"\n\n{context}"

    # Langfuse trace：整个执行节点为一条 trace，每次工具调用为子 span
    trace = langfuse.trace(name="execute", session_id=state["session_id"], input=user_input)
    span = trace.span(name="agentic_loop", input={"skill": skill_name})

    messages = [{"role": "user", "content": user_input}]
    answer = ""

    for iteration in range(MAX_ITERATIONS):
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system,
            tools=tools if tools else [],
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            # 提取文本回答
            for block in response.content:
                if hasattr(block, "text"):
                    answer = block.text
                    break
            break

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_span = trace.span(
                        name=f"tool:{block.name}",
                        input=block.input,
                        metadata={"iteration": iteration},
                    )
                    result = _call_tool(block.name, block.input, tool_span)
                    tool_span.end(output=result)

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            # 把本轮 LLM 输出 + 工具结果注回对话，进入下一轮
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
        else:
            # 未知 stop_reason，强制退出
            answer = f"[未知停止原因: {response.stop_reason}]"
            break
    else:
        answer = f"[超过最大循环次数 {MAX_ITERATIONS}，强制终止]"

    span.end(output=answer)
    trace.update(output=answer)

    # 写入短期记忆
    memory_manager.short.add(state["session_id"], "user", user_input)
    memory_manager.short.add(state["session_id"], "assistant", answer)

    # 异步写长期记忆
    import asyncio
    asyncio.create_task(
        memory_manager.long.save(state["session_id"], f"用户：{user_input}\n助手：{answer}")
    )

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

    return builder.compile(checkpointer=MemorySaver())


app = build_graph()
