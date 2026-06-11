"""
流模式控制
    1.千问不支持
    2.支持的模型可以设置：
    llm = ChatOpenAI(
    model="gpt-4",
    streaming=True,                    # Stream normal chat responses
    disable_streaming="tool_calling"   # But not tool calls
)
"""
import asyncio
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage


# 1. 定义模拟工具
@tool
def google_search(query: str) -> str:
    """当用户询问实时天气、时事新闻、或者需要联网搜索时，使用此工具。"""
    print(f"\n[系统通知] 正在后台执行工具检索: {query}...")
    if "天气" in query:
        return "北京今天晴，气温 18°C ~ 25°C，微风。"
    return "搜索到了关于该主题的最新行业报告。"


# 2. 优化模型初始化：彻底移除容易引发国内大模型 API 冲突的 disable_streaming 配置

from env_utils import API_KEY, MODEL_NAME, BASE_URL

llm = ChatOpenAI(
    model=MODEL_NAME,
    api_key=API_KEY,
    base_url=BASE_URL,
    streaming=True,
)

# 绑定工具
llm_with_tools = llm.bind_tools([google_search])


# 3. 在消费流的逻辑层做拦截（国内大模型通用安全方案）
async def run_chat_stream(user_prompt: str):
    print(f"\n用户提问: {user_prompt}")
    print("-" * 50)
    print("AI 响应: ", end="", flush=True)

    # 🌟 生产环境防崩策略：
    # 如果检测到用户提问带有明显需要用工具的倾向（或者在上层 Agent 决定要调工具时）
    # 我们主动在调用端进行降级控制，改走 ainvoke 一口气拿结果，这正是 disable_streaming 的本质工作。
    is_tool_intent = any(keyword in user_prompt for keyword in ["查", "天气", "新闻", "搜索"])

    if is_tool_intent:
        # 🟢 如果要调用工具：我们手动拦截流，走非流式的 ainvoke
        response = await llm_with_tools.ainvoke([HumanMessage(content=user_prompt)])
        if response.tool_calls:
            print(f"\n[降级拦截成功] 拦截到完整的工具调用结构，未向前端泄露任何 JSON 碎块：")
            print(response.tool_calls)
        elif response.content:
            print(response.content)
    else:
        # 🔵 正常的文本闲聊：继续保持流畅的 astream 逐字蹦字体验
        async for chunk in llm_with_tools.astream([HumanMessage(content=user_prompt)]):
            if chunk.content:
                print(chunk.content, end="", flush=True)

    print("\n" + "=" * 50)


async def main():
    # 场景 A：纯文本闲聊（正常触发流式，逐字蹦出，千问完美支持）
    await run_chat_stream("给我写一首关于春天的小诗，两句话即可。")

    # 场景 B：触发工具调用（手动拦截，防止 AsyncStream 序列化报错崩溃）
    await run_chat_stream("帮我查一下今天北京的天气怎么样？")


if __name__ == "__main__":
    asyncio.run(main())
