from fastapi import FastAPI
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from graph.workflow import app as graph_app

api = FastAPI(title="TaskPilot")


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    answer: str
    skill_used: str


@api.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    config = {"configurable": {"thread_id": req.session_id}}
    result = await graph_app.ainvoke(
        {
            "messages": [HumanMessage(content=req.message)],
            "session_id": req.session_id,
            "skill_name": "",
            "tools": [],
            "context": "",
        },
        config=config,
    )
    answer = result["messages"][-1].content
    return ChatResponse(answer=answer, skill_used=result.get("skill_name", ""))


@api.get("/skills")
def list_skills():
    from skills import SkillRegistry
    return SkillRegistry().list_skills()


@api.get("/health")
def health():
    return {"status": "ok"}
