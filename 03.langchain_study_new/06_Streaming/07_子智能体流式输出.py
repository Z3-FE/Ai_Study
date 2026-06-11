"""
subgraphs=True,  # 🌟 开启子图/子智能体事件穿透 :   强行给 API 状态机安装 X 光眼。允许深层小弟的 Token 穿透外壳丢给外层，否则底层子图会直接断流。


实际应用：

[用户]: 帮我看看波士顿的天气怎么样？

🧠 [主管]: 好的，没问题。由于需要获取实时气象数据，我正在为您
          调度后台的【天气专属助手】...
          │
          └─ ⚙️ 正在调用：call_weather_agent ("波士顿的天气")
             │
             └─ 📂【后台专家协作面板】(已展开 ───)
                🤖 当前发言：weather_agent (天气助理)
                💬 "收到主管派单。正在连接波士顿地区气象站卫星接口..."
                🔌 [卫星工具执行成功] ──> 返回: It's always sunny in Boston!
                💬 "查询完毕！波士顿那边现在总是晴空万里，非常暖和！"
"""

import asyncio
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.messages import AIMessage, AIMessageChunk, AnyMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState

from env_utils import API_KEY, MODEL_NAME, BASE_URL

model = ChatOpenAI(
    model=MODEL_NAME,
    api_key=API_KEY,
    base_url=BASE_URL
)


# =====================================================================
# 1. 定义底层专家：天气智能体（Weather Agent）及其工具
# =====================================================================

def get_weather(city: str) -> str:
    """获取指定城市的天气。"""
    return f"{city}的天气总是晴空万里！"


# 初始化天气模型

# 创建专职负责天气的子智能体，显式命名为 "weather_agent"
weather_agent = create_agent(
    model=model,
    tools=[get_weather],
    name="weather_agent",  # 🌟 官方核心：这个名字会被记录到 metadata 中
)


# 将天气智能体封装为一个可以被其他 Agent 调用的工具函数
def call_weather_agent(query: str) -> str:
    """查询天气智能体。"""
    # 子智能体采用同步 invoke 方式执行
    result = weather_agent.invoke({
        "messages": [{"role": "user", "content": query}]
    })
    return result["messages"][-1].content


# =====================================================================
# 2. 定义上层架构：主脑主管智能体（Supervisor Agent）
# =====================================================================

# 初始化主管模型

# 创建主管智能体，把刚才封装的子智能体函数当作它的“工具”喂给它
agent = create_agent(
    model=model,
    tools=[call_weather_agent],
    name="supervisor",  # 🌟 官方核心：主管的名字
)


# =====================================================================
# 3. 辅助渲染函数（汉化控制台输出格式）
# =====================================================================

def _render_message_chunk(token: AIMessageChunk) -> None:
    """处理打字机碎字输出"""
    if token.text:
        print(token.text, end="|", flush=True)  # 用 | 分割每个字
    if token.tool_call_chunks:
        print(f"\n[工具调用片段]: {token.tool_call_chunks}")


def _render_completed_message(message: AnyMessage) -> None:
    """处理节点完成后的完整消息"""
    if isinstance(message, AIMessage) and message.tool_calls:
        print(f"\n⚙️ 申请工具调用: {message.tool_calls}")
    if isinstance(message, ToolMessage):
        print(f"\n🔌 工具返回结果: {message.content_blocks}")


# =====================================================================
# 4. 核心：官方标准的多 Agent 身份识别流式循环
# =====================================================================

async def main():
    input_message = {"role": "user", "content": "波士顿的天气怎么样？"}
    current_agent = None  # 用于记录当前正在说话的 Agent 名字，防止重复打印横幅

    print("=== 🚀 启动官方 Metadata 多智能体流监听 ===")

    # 启动双模混合流监听，并开启 subgraphs=True 透传
    for chunk in agent.stream(
            {"messages": [input_message]},
            stream_mode=["messages", "updates"],
            subgraphs=True,  # 🌟 开启子图/子智能体事件穿透 :   强行给 API 状态机安装 X 光眼。允许深层小弟的 Token 穿透外壳丢给外层，否则底层子图会直接断流。
            version="v2",  # 使用 V2 协议
    ):
        # 分支 A：抓取实时蹦字（打字机碎字）
        if chunk["type"] == "messages":
            token, metadata = chunk["data"]

            # 🌟 官方示例精髓：从元数据中提取当前发言的 Agent 名字
            if agent_name := metadata.get("lc_agent_name"):
                # 如果说话的 Agent 变了，打印一行漂亮的提示横幅切换身份
                if agent_name != current_agent:
                    print(f"\n\n🤖 当前发言智能体 -> 【{agent_name}】: ")
                    current_agent = agent_name  # 更新当前发言人

            # 只有当 token 是标准的 AI 消息碎片时才渲染打字机
            if isinstance(token, AIMessageChunk):
                _render_message_chunk(token)

        # 分支 B：抓取图状态变更（完整节点事件）
        elif chunk["type"] == "updates":
            for source, update in chunk["data"].items():
                if source in ("model", "tools"):
                    _render_completed_message(update["messages"][-1])


if __name__ == "__main__":
    # 运行异步主函数
    asyncio.run(main())
