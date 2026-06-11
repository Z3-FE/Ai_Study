"""
  核心：  HumanInTheLoopMiddleware(interrupt_on={"get_weather": True}),

流式结合的优势：通过流（Stream），你可以让前端一边“打字机式”地吐出 AI 当前的思考过程和碎字，一边在后台安全地监控。
一旦走到敏感工具（如发邮件、转账），能在不破坏用户实时观感的前提下，优雅地在合适时机抛出中断信号。

实际应用：
[用户]: 帮我把下个月给老王的折扣改成 5 折。
[AI 蹦字]: 好的，我正在为您处理修改折扣的申请... (打字机效果流畅输出)
[系统拦截]: (打字机突然停住，前端收到 `__interrupt__` 信号)
[前端 UI]: 渐显弹出一个对话框 ───
         ┌────────────────────────────────────────┐
         │ 🔔 安全审批提示                        │
         │ AI 正在申请调用 `update_discount` 工具  │
         │ 参数：客户=老王, 折扣=0.5               │
         │                                        │
         │    [ 拒绝并反馈 ]   [ 修改参数 ]   [ 同意执行 ] │
         └────────────────────────────────────────┘
"""
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain.messages import AIMessage, AIMessageChunk, AnyMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command, Interrupt
from env_utils import API_KEY, MODEL_NAME, BASE_URL

model = ChatOpenAI(
    model=MODEL_NAME,
    api_key=API_KEY,
    base_url=BASE_URL
)


# 1. 定义一个模拟的天气工具（高危工具模拟）
def get_weather(city: str) -> str:
    """获取指定城市的天气。"""
    # 汉化：让返回结果更符合中文习惯
    return f"{city}的天气总是晴空万里！"


# 2. 初始化图状态的内存持久化层（有了它，程序暂停后才能被重新唤醒）
checkpointer = InMemorySaver()

# 3. 创建智能化 Agent
agent = create_agent(
    model=model,
    tools=[get_weather],
    # 🌟 核心拦截器配置：当 AI 尝试调用 "get_weather" 工具时，强制触发拦截
    middleware=[
        HumanInTheLoopMiddleware(interrupt_on={"get_weather": True}),
    ],
    checkpointer=checkpointer,
)


# 4. 辅助渲染函数：处理打字机碎字流 (messages 模式)
def _render_message_chunk(token: AIMessageChunk) -> None:
    # 如果大模型吐出了普通的文本字符
    if token.text:
        print(token.text, end="|", flush=True)  # 用 | 分割展示每个字是怎么蹦出来的
    # 如果大模型吐出的是工具调用参数的碎片
    if token.tool_call_chunks:
        print(f"\n[正在构建工具参数片段]: {token.tool_call_chunks}")


# 5. 辅助渲染函数：处理节点完成后的完整消息 (updates 模式)
def _render_completed_message(message: AnyMessage) -> None:
    # 如果是 AI 发出的消息，并且里面包含了工具调用申请
    if isinstance(message, AIMessage) and message.tool_calls:
        print(f"\n📢 [AI 决策] 申请调用工具: {message.tool_calls}")
    # 如果是工具执行完后返回的结果
    if isinstance(message, ToolMessage):
        print(f"\n🛠️ [工具返回] 执行结果: {message.content_blocks}")


# 6. 辅助渲染函数：处理拦截中断信号 (updates 模式)
def _render_interrupt(interrupt: Interrupt) -> None:
    interrupts = interrupt.value
    # 遍历当前被扣留的所有动作请求，打印给人看
    for request in interrupts["action_requests"]:
        print(f"\n🛑 [风控警报] 触发人工审批！请求原因: {request['description']}")


# 7. 模拟用户输入（汉化：询问波士顿和旧金山的天气）
input_message = {
    "role": "user",
    "content": "你能帮我查一下波士顿和旧金山的天气吗？",
}

# 必须提供 thread_id（线程ID），这样内存层才知道把这个暂停的对话存在哪
config = {"configurable": {"thread_id": "crm_test_001"}}
interrupts = []

print("=== 🚀 Agent 开始流式执行 ===")

# 8. 启动双模混合流监听
for chunk in agent.stream(
        {"messages": [input_message]},
        config=config,
        stream_mode=["messages", "updates"],  # 混合监听：1.碎字 2.状态更新
        version="v2",
):
    # 分支 A：抓取大模型逐字吐出的 Token
    if chunk["type"] == "messages":
        token, metadata = chunk["data"]
        if isinstance(token, AIMessageChunk):
            _render_message_chunk(token)

    # 分支 B：抓取图节点层面的状态迁移和拦截信号
    elif chunk["type"] == "updates":
        for source, update in chunk["data"].items():
            # 情况 1：如果是模型或者工具节点跑完了，打印其阶段性完整结果
            if source in ("model", "tools"):
                _render_completed_message(update["messages"][-1])

            # 情况 2：最核心！抓取到了中间件丢出来的 __interrupt__（中断）
            if source == "__interrupt__":
                interrupts.extend(update)  # 把中断事件记录下来
                _render_interrupt(update[0])  # 打印审批单

print("\n=== 🛑 流程已冻结，等待人类决策 ===")
