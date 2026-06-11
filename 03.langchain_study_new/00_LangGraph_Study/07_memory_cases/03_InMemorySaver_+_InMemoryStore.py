import re
from dataclasses import dataclass

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import MessagesState, START, StateGraph
from langgraph.runtime import Runtime
from langgraph.store.memory import InMemoryStore


@dataclass
class Context:
    user_id: str


def extract_name_from_thread(messages) -> str | None:
    """优先从当前线程消息历史里找名字。"""
    for message in messages:
        if isinstance(message, HumanMessage):
            # 正则 如果找到，返回匹配结果对象, 如果没找到，返回 None
            match = re.search(r"我叫(?!什么)([A-Za-z\u4e00-\u9fa5·\-]{1,30})", message.content)
            if match:
                return match.group(1)  # 获取名称
    return None


# 参数定义位置没有顺序，建议
def chat_node(state: MessagesState, runtime: Runtime[Context], config: RunnableConfig):
    """
    这个案例同时演示两层记忆：
    1. InMemorySaver: 同一 thread_id 下保留消息历史（短期记忆）
    2. InMemoryStore: 同一进程内，跨 thread 共享用户资料（长期/共享记忆）
    """
    print(runtime)
    print(f"config: {config}")
    user_id = runtime.context.user_id
    namespace = (user_id, "profile")
    last_human = next((m for m in reversed(state["messages"]) if isinstance(m, HumanMessage)), None)
    if last_human is None:
        return {"messages": [AIMessage(content="我还没收到你的消息。")]}

    text = last_human.content.strip()
    match = re.search(r"我叫(?!什么)([A-Za-z\u4e00-\u9fa5·\-]{1,30})", text)
    if match:
        name = match.group(1)
        runtime.store.put(namespace, "name", {"name": name})
        return {
            "messages": [
                AIMessage(
                    content=f"记住了，你叫{name}。我已经写入当前线程记忆，也同步到共享 store。"
                )
            ]
        }

    if "我叫什么" in text:
        # 先看当前线程历史，命中则说明是短期记忆
        name = extract_name_from_thread(state["messages"])
        if name:
            return {"messages": [AIMessage(content=f"你叫{name}。这次命中的是当前线程的短期记忆。")]}

        # 当前线程没有，再去共享 store 里查，说明是跨线程共享记忆
        item = runtime.store.get(namespace, "name")
        if item:
            return {"messages": [AIMessage(content=f"你叫{item.value['name']}。这次命中的是共享 store 记忆。")]}

        return {"messages": [AIMessage(content="当前线程和共享 store 里都还没有你的名字。")]}

    return {"messages": [AIMessage(content="收到。你可以先说“我叫Bob”，再问“我叫什么名字？”。")]}


builder = StateGraph(MessagesState, context_schema=Context)
builder.add_node("chat", chat_node)
builder.add_edge(START, "chat")

app = builder.compile(
    checkpointer=InMemorySaver(),
    store=InMemoryStore(),
)

# 同一个 user_id，不同 thread_id
thread_1 = {"configurable": {"thread_id": "thread-1"}}
thread_2 = {"configurable": {"thread_id": "thread-2"}}
thread_3 = {"configurable": {"thread_id": "thread-3"}}

same_user = Context(user_id="user-001")
other_user = Context(user_id="user-002")

app.invoke(
    {"messages": [HumanMessage(content="你好，我叫Bob")]},
    thread_1,
    context=same_user,
)

r1 = app.invoke(
    {"messages": [HumanMessage(content="我叫什么名字？")]},
    thread_1,
    context=same_user,
)
r2 = app.invoke(
    {"messages": [HumanMessage(content="我叫什么名字？")]},
    thread_2,
    context=same_user,
)
r3 = app.invoke(
    {"messages": [HumanMessage(content="我叫什么名字？")]},
    thread_3,
    context=other_user,
)

print("同线程追问：", r1["messages"][-1].content)
print("跨线程但同用户：", r2["messages"][-1].content)
print("换用户后：", r3["messages"][-1].content)
