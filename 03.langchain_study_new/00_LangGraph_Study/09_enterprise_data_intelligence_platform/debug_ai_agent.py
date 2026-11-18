import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "ai_agent.app:app",
        host="127.0.0.1",
        port=8010,
        reload=False,
    )
