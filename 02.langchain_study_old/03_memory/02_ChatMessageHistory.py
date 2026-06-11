from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory

# 旧方法
history = ChatMessageHistory()

history.add_user_message('hello world')
history.add_ai_message('很高兴见到你')

print(type(history))  # <class 'langchain_core.chat_history.InMemoryChatMessageHistory'>
print(history)

print(history.messages)

# 1.0新调用
InMemoryChatMessageHistory()
