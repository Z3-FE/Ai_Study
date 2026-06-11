"""对比 llm 与 agent 的 streaming 效果

常见 stream_mode 说明：
1. values
   返回当前完整 state，适合看“现在完整状态是什么”。

2. updates
   返回每一步的状态更新，适合看“这一步改了什么”。

3. messages
   返回模型输出的 token 流，适合做打字机效果。

4. custom
   返回自定义流事件，需要在 tool 或节点里主动调用 writer(...)。
   常用于告诉用户“工具正在做什么”，例如：
   - 开始搜索资料
   - 正在查询数据库
   - 正在整理答案

5. checkpoints
   返回 checkpoint 事件，也就是状态快照被保存时的数据。
   适合学习 memory / checkpointer 的工作过程。

6. tasks
   返回任务级别的执行事件，适合看“任务发生了什么”。

7. debug
   返回更细粒度的调试信息，适合排查执行过程中的问题。

一句话速记：
- messages: 模型正在说什么
- updates: 这一步改了什么
- values: 当前完整状态是什么
- custom: 我主动发了什么过程提示
- checkpoints: 状态何时被保存
- tasks: 任务发生了什么
- debug: 系统内部是怎么跑的
"""
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.config import get_stream_writer

from env_utils import MODEL_NAME, API_KEY, BASE_URL

model = ChatOpenAI(
    model=MODEL_NAME,
    api_key=API_KEY,
    base_url=BASE_URL,
)


@tool
def explain_ai(topic: str) -> str:
    """解释一个主题。"""
    writer = get_stream_writer()
    writer("开始整理资料...")
    writer(f"正在解释主题: {topic}")
    writer("马上生成最终答案...")
    return f"{topic} 是研究如何让机器模拟人类智能能力的技术。"


def print_llm_response():
    for chunk in model.stream('你好'):
        print(chunk.text, end="", flush=True)


def print_agent_response(stream_mode, tools: list, checkpointer=None):
    print(f'正在执行stream_mode={stream_mode}')
    agent = create_agent(
        model=model,
        tools=[*tools],
        middleware=[],
        checkpointer=checkpointer if checkpointer else None,
        system_prompt=(
            "你是一个专业的助手。"
        ),
    )
    config: RunnableConfig = {"configurable": {"thread_id": "combined_demo_1"}}

    for chunk in agent.stream(
            {"messages": [{"role": "user", "content": "请使用 explain_ai 工具介绍一下人工智能"}]},
            stream_mode=stream_mode,
            config=config if checkpointer else None
    ):
        if isinstance(stream_mode, list):
            mode, data = chunk
            print(f"[{mode}] {data}")
        else:
            print(chunk)


if __name__ == "__main__":
    stream_mode = ("values",  # 返回整体messagelist，包含user的输入
                   "updates",  # 返回最后的ai信息
                   "messages",  # 返回最后的ai信息 并且 返回每次更新的内容，相当于一个字一个字的打印
                   "custom",  # 只返回自定义流事件
                   ["custom", "messages"],  # 同时返回自定义流事件和模型 token 输出
                   "checkpoints",  # 可以打印每次状态快照流式发出来（需要checkpointer：InMemorySaver()）设置的用户信息。
                   "tasks",  # 返回的数据会很直观的先给id 信息，更加清晰
                   "debug")  # 会返回'step': 1,。。。。更加清晰

    input_data = input(
        "请输入streaming模式： 1.values 2.updates 3.messages 4.custom 5.custom+messages 6.checkpoints 7.tasks 8.debug，其他输入执行llm的streaming效果\n")
    if input_data.isdigit() and 1 <= int(input_data) <= len(stream_mode):
        if input_data in {"4", "5"}:
            print_agent_response(stream_mode[int(input_data) - 1], [explain_ai], None)
        elif input_data in {"6"}:
            print_agent_response(stream_mode[int(input_data) - 1], [], checkpointer=InMemorySaver())
        else:
            print_agent_response(stream_mode[int(input_data) - 1], [], None)
    else:
        print("执行llm的streaming效果")
        print_llm_response()
