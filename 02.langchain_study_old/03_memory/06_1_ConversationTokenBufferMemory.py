import os
from typing import List
import tiktoken
from langchain_classic.memory import ConversationTokenBufferMemory, ConversationSummaryMemory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from typing import Any, Callable
from langchain_core.messages import get_buffer_string
from langchain_classic.memory.chat_memory import BaseChatMemory

# --- 配置 LLM (使用占位符) ---
API_KEY = os.environ.get("API_KEY", "YOUR_API_KEY")
BASE_URL = os.environ.get("BASE_URL", "https://api.deepseek.com/v1")
MODEL_NAME = "deepseek-reasoner"
TEMPERATURE = 0.5

os.environ["OPENAI_API_KEY"] = API_KEY
os.environ["OPENAI_BASE_URL"] = BASE_URL

llm = ChatOpenAI(
    model=MODEL_NAME,
    temperature=TEMPERATURE,
)
print(f"✅ 模型 '{llm.model_name}' 初始化成功。")
print("-" * 50)

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


llm = ChatOpenAIManualCount(
    model=MODEL_NAME,
    temperature=TEMPERATURE,
)

memory = ConversationTokenBufferMemory(
    llm=llm,
    max_token_limit=50,
    return_messages=True,
)

# 验证 Token 计数和截断功能
memory.save_context({"input": "你好"}, {"output": "我很好，谢谢"})  # 约 10 tokens
memory.save_context({"input": "帮我算一下1+1等于几？"}, {"output": "2"})  # 约 10 tokens

# 假设总计 20 tokens，如果再添加，应该会截断第一轮对话
print(f"当前 Token 计数：{llm.get_num_tokens_from_messages(memory.buffer)}")

# 尝试添加超过限制的消息，应该触发截断
memory.save_context({"input": "这个消息应该会触发截断"}, {"output": "这条回复很长，超过了 20 tokens 限制"})

print(f"截断后的 Token 计数：{llm.get_num_tokens_from_messages(memory.buffer)}")
print(memory.load_memory_variables({}))
