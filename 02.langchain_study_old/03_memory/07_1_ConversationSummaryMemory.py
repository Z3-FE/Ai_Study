"""
定期将旧的对话内容通过 LLM 总结成一个不断更新的“摘要”（Summary），并用这个摘要来代表所有历史记录。
"""

import os

from langchain_classic.memory import ConversationSummaryMemory
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_openai import ChatOpenAI

from langchain_study.env_utils import MODEL_NAME, API_KEY, BASE_URL, TEMPERATURE

# --- 配置 LLM ---
os.environ["OPENAI_API_KEY"] = API_KEY
os.environ["OPENAI_BASE_URL"] = BASE_URL

# LLM 实例，用于 Chat 和生成摘要
llm = ChatOpenAI(
    model=MODEL_NAME,
    temperature=TEMPERATURE,
)
print(f"✅ 模型 '{llm.model_name}' 初始化成功。")
print("-" * 50)

history = InMemoryChatMessageHistory()
history.add_user_message('你是谁')
history.add_user_message('你是人工助手小智')
memory = ConversationSummaryMemory(llm=llm, chat_memory=history, return_messages=True)

# 验证 Token 计数和截断功能
memory.save_context({"input": "你好"}, {"output": "我很好，谢谢"})
memory.save_context({"input": "帮我算一下1+1等于几？"}, {"output": "2"})

print(memory.load_memory_variables({}))  # 获取摘要
print("-" * 50)

# 记录了历史的交互信息
print(memory.chat_memory.messages)
