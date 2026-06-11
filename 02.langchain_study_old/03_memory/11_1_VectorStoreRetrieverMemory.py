import os
import sys

# 将项目根目录添加到 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from langchain_community.vectorstores import Chroma
from langchain_classic.memory import VectorStoreRetrieverMemory
from langchain_classic.chains.conversation.base import ConversationChain
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import PromptTemplate

from langchain_study.env_utils import API_KEY, BASE_URL, MODEL_NAME, TEMPERATURE, EMBEDDING_MODEL_NAME

# --- 配置 LLM 和 Embeddings ---
os.environ["OPENAI_API_KEY"] = API_KEY
os.environ["OPENAI_BASE_URL"] = BASE_URL

print("--- 初始化组件 ---")

# 1. 初始化 Embeddings
# 注意：这里假设  提供了兼容 OpenAI 格式的 Embeddings API。
# 如果  不支持 Embeddings，或者模型名称不同，这里可能会报错。
# 常见替代方案是使用 HuggingFaceEmbeddings (本地) 或 OpenAI 原生 Embeddings。
try:
    print("⏳ 正在测试  Embeddings API...")
    embeddings = OpenAIEmbeddings(
        model=EMBEDDING_MODEL_NAME,
        base_url=BASE_URL,
        api_key=API_KEY,
        check_embedding_ctx_length=False
    )
    # 尝试生成一次 Embedding 以验证 API 是否可用
    embeddings.embed_query("test")
    print("✅  Embeddings API 可用")
except Exception as e:
    print(f"❌  Embeddings API 调用失败: {e}")
    print("⚠️ 自动回退到 FakeEmbeddings (注意：这将导致检索结果随机，仅用于演示代码结构)")
    from langchain_core.embeddings import FakeEmbeddings

    # FakeEmbeddings 生成随机向量，因此相似度搜索将返回随机结果
    embeddings = FakeEmbeddings(size=768)

# 2. 初始化 VectorStore (使用 Chroma)
# 我们使用内存模式 (没有 persist_directory)，重启后数据丢失
vectorstore = Chroma(embedding_function=embeddings)
print("✅ VectorStore (Chroma) 初始化")

# 3. 初始化 Retriever
# 设置 k=1，表示每次只检索最相关的 1 条历史记录
retriever = vectorstore.as_retriever(search_kwargs=dict(k=1))

# 4. 初始化 VectorStoreRetrieverMemory
memory = VectorStoreRetrieverMemory(retriever=retriever)

# 5. 初始化 LLM
llm = ChatOpenAI(
    model=MODEL_NAME,
    temperature=TEMPERATURE,
    verbose=True
)

# 6. 定义 Prompt
# VectorStoreRetrieverMemory 默认将检索到的文档放入 "history" 变量
template = """你是一个友好的 AI 助手。
以下是与当前输入相关的上下文信息：
{history}

Human: {input}
AI:"""
PROMPT = PromptTemplate(input_variables=["history", "input"], template=template)

# 7. 初始化 ConversationChain
conversation = ConversationChain(
    llm=llm,
    memory=memory,
    prompt=PROMPT,
    verbose=True
)

print("-" * 50)
print("--- 启动会话：观察基于向量检索的记忆 ---")

# --- 场景模拟 ---

# 轮次 1：告诉 AI 一些关于用户的细节
print("\n>>> 轮次 1：输入事实信息")
# 这些信息会被存入 VectorStore
conversation.predict(input="我最喜欢的食物是烤鸭。")
conversation.predict(input="我最喜欢的运动是篮球。")
conversation.predict(input="我养了一只叫‘小白’的狗。")
print("[系统] 已输入三条事实信息。")

# 轮次 2：聊一些无关的话题，通过 k=1 限制，观察是否会检索到旧信息
print("\n>>> 轮次 2：无关话题")
conversation.predict(input="今天天气真不错，适合出去玩。")

# 轮次 3：询问之前的特定信息
# Memory 应该通过 Vector Search 检索到 "烤鸭" 相关的信息
print("\n>>> 轮次 3：询问特定信息 (测试检索能力)")
print("Human: 我最喜欢的食物是什么？")
response = conversation.predict(input="我最喜欢的食物是什么？")
print(f"[AI 助手]: {response}")

# 验证：手动检查检索结果
print("\n[调试] 手动检索 '食物':")
docs = vectorstore.similarity_search("食物", k=1)
for doc in docs:
    print(f"Found doc: {doc.page_content}")

print("-" * 50)
