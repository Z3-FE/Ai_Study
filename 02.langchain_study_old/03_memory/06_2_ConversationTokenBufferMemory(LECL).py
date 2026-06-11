import os
import tiktoken
from typing import Dict, List, Any, Callable

from langchain_classic.base_memory import BaseMemory
from langchain_classic.memory.chat_memory import BaseChatMemory
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, get_buffer_string
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables import RunnableConfig
from langchain_classic.memory import ConversationTokenBufferMemory
from langchain_core.callbacks.base import BaseCallbackHandler

from langchain_study.env_utils import MODEL_NAME, API_KEY, BASE_URL, TEMPERATURE

# --- 占位符配置 (请确保在环境中设置了有效值) ---


MAX_TOKEN_LIMIT = 100  # 设定一个较小的 Token 限制，方便测试截断

# --- 配置 LLM ---
os.environ["OPENAI_API_KEY"] = API_KEY
os.environ["OPENAI_BASE_URL"] = BASE_URL

# LLM 实例，用于 Chat 和生成摘要
llm = ChatOpenAI(
    model=MODEL_NAME,
    temperature=TEMPERATURE,
)
print(f"✅ 模型 '{llm.model_name}' 初始化成功。")
print(f"✅ 最大 Token 限制 MAX_TOKEN_LIMIT={MAX_TOKEN_LIMIT}")
print("-" * 50)

# --- 核心修正：手动定义 Token 计数函数 ---

# 使用 gpt-4 的编码器进行 Token 计数，以近似 DeepSeek 的 Token 数量
TOKEN_ENCODER = tiktoken.encoding_for_model("gpt-4")


def count_tokens_manually(messages: List[BaseMessage]) -> int:
    """
    一个自定义的 Token 计数函数，用于兼容非 OpenAI 模型。
    它将 BaseMessage 列表转换为 tiktoken 可以处理的格式。
    """
    total_tokens = 0
    # 模拟 tiktoken 对 LangChain BaseMessage 列表的计数逻辑
    # 注意：这个转换并不完美，但足以用于记忆截断的近似计数
    for message in messages:
        # LangChain 消息包含类型和内容
        # 计入角色名称的 tokens (如 'user', 'assistant')
        if isinstance(message, HumanMessage):
            role_prefix = "user"
        elif isinstance(message, AIMessage):
            role_prefix = "assistant"
        else:
            role_prefix = "system"  # 忽略其他类型消息

        # 将角色前缀和内容编码
        tokens_content = TOKEN_ENCODER.encode(message.content)
        tokens_role = TOKEN_ENCODER.encode(role_prefix)

        # 简单相加，并增加一些 overhead (例如 4 tokens/message)
        total_tokens += len(tokens_content) + len(tokens_role) + 4

    return total_tokens


class ManualTokenBufferMemory(BaseChatMemory):
    human_prefix: str = "Human"
    ai_prefix: str = "AI"
    memory_key: str = "history"
    max_token_limit: int = 2000
    token_counter: Callable[[list[BaseMessage]], int]

    @property
    def buffer(self) -> Any:
        return (
            self.chat_memory.messages
            if self.return_messages
            else get_buffer_string(
                self.chat_memory.messages,
                human_prefix=self.human_prefix,
                ai_prefix=self.ai_prefix,
            )
        )

    @property
    def memory_variables(self) -> list[str]:
        return [self.memory_key]

    def load_memory_variables(self, inputs: dict[str, Any]) -> dict[str, Any]:
        return {self.memory_key: self.buffer}

    def save_context(self, inputs: dict[str, Any], outputs: dict[str, str]) -> None:
        super().save_context(inputs, outputs)
        buffer = self.chat_memory.messages
        curr_buffer_length = self.token_counter(buffer)
        if curr_buffer_length > self.max_token_limit:
            while curr_buffer_length > self.max_token_limit and buffer:
                buffer.pop(0)
                curr_buffer_length = self.token_counter(buffer)

    @property
    def buffer_token_length(self) -> int:
        return self.token_counter(self.chat_memory.messages)


class ChatOpenAIManualCount(ChatOpenAI):
    def get_num_tokens_from_messages(self, messages: List[BaseMessage]) -> int:
        return count_tokens_manually(messages)


# token解析

llm = ChatOpenAIManualCount(
    model=MODEL_NAME,
    temperature=TEMPERATURE,
)


def count_tokens_manually(messages: List[BaseMessage]) -> int:
    """
    自定义的 Token 计数函数，用于绕过 ChatOpenAI 上的未实现方法。
    """
    total_tokens = 0
    # 模拟 LangChain/tiktoken 的计数逻辑 (约 4 tokens overhead per message)
    for message in messages:
        # 将角色名称和内容编码并相加
        content_tokens = TOKEN_ENCODER.encode(message.content)
        total_tokens += len(content_tokens) + 4

    return total_tokens


# --- 1. 历史记录存储后端 (基于 Session ID) ---

# 使用 Dict 存储每个 session ID 的 ConversationTokenBufferMemory 实例
session_store: Dict[str, BaseMemory] = {}
MEMORY_KEY = "chat_history"


def get_token_buffer_history(session_id: str) -> ConversationTokenBufferMemory:
    """
    为每个 session ID 创建或返回一个独立的 ConversationTokenBufferMemory 实例。
    """
    if session_id not in session_store:
        print(f"** 📝 创建新的 Token 缓冲记忆实例 (Session ID: {session_id}) **")
        session_store[session_id] = ConversationTokenBufferMemory(
            llm=llm,  # 用于生成摘要的 LLM
            max_token_limit=MAX_TOKEN_LIMIT,
            memory_key=MEMORY_KEY,
            return_messages=True,  # 确保返回消息列表给 Prompt 的 placeholder
            token_counter=count_tokens_manually  # 强制使用自定义计数器
        )
    # RWMH 需要 BaseMessageHistory 接口，我们返回 03_memory 实例的 chat_memory 属性
    return session_store[session_id].chat_memory


# --- 2. 定义 LCEL Prompt 和 Base Chain ---

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", f"你是一个善于总结的助手。请注意：你的记忆限制在 {MAX_TOKEN_LIMIT} Token 内。"),
        # 使用 placeholder 接收 List[BaseMessage]
        ("placeholder", f"{{{MEMORY_KEY}}}"),
        ("human", "{input}"),
    ]
)

# Base Chain：无需 RunnablePassthrough，因为记忆组件自己管理截断和摘要
base_chain = prompt | llm | StrOutputParser()

# --- 3. 使用 RunnableWithMessageHistory 封装 ---

chain_with_history = RunnableWithMessageHistory(
    runnable=base_chain,
    get_session_history=get_token_buffer_history,  # 传入工厂函数
    input_messages_key="input",
    history_messages_key=MEMORY_KEY,  # 必须与 memory_key="chat_history" 一致
)


# --- 开启最小化日志回调 ---
class MinimalPromptCallbackHandler(BaseCallbackHandler):
    @property
    def ignore_chain(self) -> bool:
        return True

    @property
    def ignore_retriever(self) -> bool:
        return True

    @property
    def ignore_agent(self) -> bool:
        return True

    @property
    def ignore_custom_event(self) -> bool:
        return True

    def on_chat_model_start(self, serialized: dict, messages: List[List[BaseMessage]], **kwargs: Any) -> Any:
        batch = messages[0] if messages else []
        # 仅打印最后一条 Human 和 System（若存在）
        system = next((m for m in batch if
                       isinstance(m, type(HumanMessage(content=''))).__class__.__mro__[1] is AIMessage and False), None)
        last_human = next((m for m in reversed(batch) if isinstance(m, HumanMessage)), None)
        if last_human:
            print(f"[prompt] human: {last_human.content}")
        # 打印 system（如果确有）
        for m in batch:
            if m.__class__.__name__ == "SystemMessage":
                print(f"[prompt] system: {m.content}")
                break

    def on_llm_end(self, response: Any, **kwargs: Any) -> Any:
        try:
            gens = getattr(response, "generations", [])
            if gens and gens[0]:
                first = gens[0][0]
                text = getattr(first, "text", None)
                if text is None:
                    msg = getattr(first, "message", None)
                    text = getattr(msg, "content", "")
                print(f"[llm] {text}")
        except Exception:
            pass


print(f"✅ RunnableWithMessageHistory 封装完成，记忆键名：{MEMORY_KEY}")
print("-" * 50)


# --- 4. 运行测试会话 ---

def run_token_buffer_test(session_id: str):
    """运行 Token 缓冲记忆测试，观察摘要生成"""
    print(f"\n--- 正在启动会话: {session_id} (Token Limit: {MAX_TOKEN_LIMIT}) ---")

    config: RunnableConfig = {"configurable": {"session_id": session_id}}
    # 注意：get_token_buffer_history 返回的是 chat_memory，但我们可以在 session_store 中获取完整的实例
    get_token_buffer_history(session_id)
    # 获取记忆实例以便观察
    memory_instance = session_store[session_id]

    # --- 轮次 1：建立基础记忆 ---
    query_1 = "我的名字叫艾利克斯，我有一只金毛猎犬。"
    chain_with_history.with_config(callbacks=[MinimalPromptCallbackHandler()]).invoke({"input": query_1}, config=config)
    print(f"[状态 1] 当前 Token: {llm.get_num_tokens_from_messages(memory_instance.chat_memory.messages)}")
    print("-" * 50)

    # --- 轮次 2：继续添加记忆 ---
    query_2 = "我最喜欢的城市是多伦多，因为那里有很多湖泊和公园。"
    chain_with_history.with_config(callbacks=[MinimalPromptCallbackHandler()]).invoke({"input": query_2}, config=config)
    print(f"[状态 2] 当前 Token: {llm.get_num_tokens_from_messages(memory_instance.chat_memory.messages)}")
    print("-" * 50)

    # --- 轮次 3：触发截断和摘要生成 (故意使用长消息) ---
    query_3 = "现在，请你详细描述一下：为什么说 Token 缓冲记忆比窗口记忆更复杂？请用 50 个字解释。"
    # 这一轮的输入和输出很可能导致总 Token 超过 100，触发摘要生成
    # 观察 Verbose 日志中 LLM 生成 Summary 的过程
    chain_with_history.with_config(callbacks=[MinimalPromptCallbackHandler()]).invoke({"input": query_3}, config=config)
    print(f"[状态 3] **截断后** Token: {llm.get_num_tokens_from_messages(memory_instance.chat_memory.messages)}")

    # --- 轮次 4：验证摘要是否生效 ---
    print("\n--- 轮次 4：验证摘要 (问第一轮的问题) ---")
    query_4 = "你还记得我的狗叫什么名字吗？"
    # 此时，03_memory.chat_memory.messages 的开头应该是 "SystemMessage: 这是一个摘要..."
    chain_with_history.with_config(callbacks=[MinimalPromptCallbackHandler()]).invoke({"input": query_4}, config=config)


# 运行测试
run_token_buffer_test("token_buffer_user_001")
