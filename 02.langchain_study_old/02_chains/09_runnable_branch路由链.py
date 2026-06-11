import os
import re
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableBranch
from langchain_openai import ChatOpenAI
from langchain_classic.chains.combine_documents import create_stuff_documents_chain

from langchain_study.env_utils import (
    API_KEY,
    BASE_URL,
    MODEL_NAME,
    TEMPERATURE,
)


def is_math_question(text: str) -> bool:
    return bool(re.search(r"[0-9]", text) and re.search(r"[+\-*/()]+", text))


def safe_eval(expr: str) -> float:
    cleaned = re.sub(r"[^0-9+\-*/(). ]", "", expr)
    return eval(cleaned, {"__builtins__": {}}, {})


def main():
    os.environ["OPENAI_API_KEY"] = API_KEY
    os.environ["OPENAI_BASE_URL"] = BASE_URL

    llm = ChatOpenAI(model=MODEL_NAME, temperature=TEMPERATURE)

    doc_prompt = ChatPromptTemplate.from_messages([
        ("system", "你是文档问答助手，只根据上下文回答。"),
        ("human", "上下文:\n{context}\n问题：{input}"),
    ])
    docs = [
        Document(page_content="文档路由示例：当问题不是数学计算时，走文档问答。"),
    ]
    doc_chain = create_stuff_documents_chain(llm, doc_prompt)

    math_prompt = ChatPromptTemplate.from_messages([
        ("system", "将中文问题转为只包含四则运算的表达式，不要解释。"),
        ("human", "问题：{input}"),
    ])

    def run_math(inp: dict):
        q = inp["input"]
        expr = llm.invoke(math_prompt.invoke({"input": q}).to_messages()).content
        expr = re.sub(r"^```(?:text|plain)?\n|```$", "", expr).strip()
        value = safe_eval(expr)
        return f"表达式: {expr}\n结果: {value}"

    router = RunnableBranch(
        (lambda x: is_math_question(x.get("input", "")), run_math),
        doc_chain,
    )

    q1 = "1+2*3 等于多少？"
    print("[数学问题]", q1)
    print(router.invoke({"input": q1, "context": docs}))

    q2 = "本示例中的路由逻辑是什么？"
    print("[文档问题]", q2)
    print(router.invoke({"input": q2, "context": docs}))


if __name__ == "__main__":
    main()
