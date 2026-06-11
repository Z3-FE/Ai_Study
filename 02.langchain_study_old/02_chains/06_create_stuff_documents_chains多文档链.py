"""
Map-Reduce：先对每份文档分别“Map”（独立总结要点），再“Reduce”（合并这些要点做推理）得到最终回答。
Map-Reduce：文档多或很长，需要可扩展的分而治；更适合长文本/大量文档
Map-Reduce：多次调用（每文档一次 + 合并一次），延迟与费用更高；但在大语料下更稳、更可控。
"""

import os

from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from langchain_study.env_utils import (
    API_KEY,
    BASE_URL,
    MODEL_NAME,
    TEMPERATURE,
)


def main():
    os.environ["OPENAI_API_KEY"] = API_KEY
    os.environ["OPENAI_BASE_URL"] = BASE_URL

    llm = ChatOpenAI(model=MODEL_NAME, temperature=TEMPERATURE)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是知识问答助手，根据给定上下文回答问题。只用中文，无法回答则说不知道。"),
        ("human", "上下文:\n{context}\n问题：{input}"),
    ])

    docs = [
        Document(page_content="LangChain 是一个用于构建 LLM 应用的框架。"),
        Document(page_content="Stuff 文档链会将多个文档直接拼接为一个上下文传给模型。"),
        Document(page_content="在中文场景中，合理的提示词能显著提升回答质量。"),
    ]

    chain = create_stuff_documents_chain(llm, prompt)

    question = "什么是 Stuff 文档链？它如何使用？"
    print(f"[输入问题] {question}")
    result = chain.invoke({"input": question, "context": docs})
    print(f"[模型回答] {result}")


if __name__ == "__main__":
    main()
