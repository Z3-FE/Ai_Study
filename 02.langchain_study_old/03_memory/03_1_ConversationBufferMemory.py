import os

from langchain_classic.chains.conversation.base import ConversationChain
from langchain_classic.chains.llm import LLMChain
from langchain_classic.memory import ConversationBufferMemory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI

# 导入 DeepSeek 配置
from langchain_study.env_utils import API_KEY, BASE_URL, MODEL_NAME, TEMPERATURE

# --- 配置 LLM ---
os.environ["OPENAI_API_KEY"] = API_KEY
os.environ["OPENAI_BASE_URL"] = BASE_URL
llm = ChatOpenAI(
    model=MODEL_NAME,
    temperature=TEMPERATURE,
)
print(f"✅ 模型 '{llm.model_name}' 初始化成功。")
print("-" * 50)

memory_convers = ConversationBufferMemory()

# 字典里边的key可以随便命名
memory_convers.save_context(inputs={"03_embeddings": "human"}, outputs={"ai": '你好'})
memory_convers.save_context(inputs={"03_embeddings": "帮我算一下1+1等于几？"}, outputs={"ai": '2'})

# 返回str
print(memory_convers.load_memory_variables({}))

# 返回list
print(memory_convers.chat_memory.messages)

# 返回list 第二种
memory_convers2 = ConversationBufferMemory(return_messages=True)  # 返回list

# 字典里边的key可以随便命名
memory_convers2.save_context(inputs={"03_embeddings": "我的名字叫小明"}, outputs={"ai": '你好'})
memory_convers2.save_context(inputs={"03_embeddings": "帮我算一下1+1等于几？"}, outputs={"ai": '2'})

print(memory_convers2.load_memory_variables({}))  # {'history': [....]}
print(type(memory_convers2.load_memory_variables({})))  # <class 'dict'>

prompt = ChatPromptTemplate([
    ("system", "你是一个人工智能助手"),
    MessagesPlaceholder(variable_name="history"),  # 因为ConversationBufferMemory 返回的就是history为key
    ("human", "{03_embeddings}"),
])

chain = LLMChain(prompt=prompt, llm=llm, memory=memory_convers2)
response = chain.invoke({'03_embeddings': '我叫什么？'})
print(response)
