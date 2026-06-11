"""
ConversationBufferWindowMemory 的核心作用是解决
Token 爆炸问题：它只记住最近的 $K$ 轮对话，自动丢弃最旧的对话，从而将 Prompt 的长度限制在一个可控的窗口内。

"""

from langchain_classic.memory import ConversationBufferWindowMemory

"""
03_memory = ConversationBufferWindowMemory(k=2)  # K：限制输出最后几次聊天记录

03_memory.save_context(inputs={"input": '你好1'}, outputs={"output": "你好1输出"})
03_memory.save_context(inputs={"input": '你好2'}, outputs={"output": "你好2输出"})
03_memory.save_context(inputs={"input": '你好3'}, outputs={"output": "你好3输出"})

print(03_memory.chat_memory.messages)  # 会输出全部信息
print(03_memory.load_memory_variables({}))  # 会收到k值的限制

"""
