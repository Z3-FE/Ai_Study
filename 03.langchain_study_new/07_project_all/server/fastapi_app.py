"""最小 FastAPI 接口版

作用：
1. 把 LangChain agent 暴露成 HTTP 接口
2. 方便前端通过 fetch / axios 调用

运行前建议先安装：
uv add fastapi uvicorn

启动：
uvicorn 07_project_all.server.fastapi_app:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .agent import agent


app = FastAPI(title="LangChain Frontend Demo API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    thread_id: str = "frontend_api_demo_1"


class ChatResponse(BaseModel):
    reply: str
    thread_id: str


@app.get("/health")
def health():
    """健康检查接口。"""
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """最简单的一次对话接口。

    请求：
    {
      "message": "请查询北京天气",
      "thread_id": "demo_1"
    }
    """
    result = agent.invoke(
        {"messages": [{"role": "user", "content": request.message}]},
        config={"configurable": {"thread_id": request.thread_id}},
    )
    last_message = result["messages"][-1]
    return ChatResponse(
        reply=str(last_message.content),
        thread_id=request.thread_id,
    )
