import os
import re
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from langchain_study.env_utils import (
    API_KEY,
    BASE_URL,
    MODEL_NAME,
    TEMPERATURE,
)


def safe_eval(expr: str) -> float:
    cleaned = re.sub(r"[^0-9+\-*/(). ]", "", expr)
    return eval(cleaned, {"__builtins__": {}}, {})


def main():
    os.environ["OPENAI_API_KEY"] = API_KEY
    os.environ["OPENAI_BASE_URL"] = BASE_URL

    llm = ChatOpenAI(model=MODEL_NAME, temperature=TEMPERATURE)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "仅输出算式表达式，如 (1+2*3)/4，不要解释和单位。"),
        ("human", "问题：{input}"),
    ])

    question = "(10-3)*2 + 4/2 等于多少？"
    print(f"[问题] {question}")
    messages = prompt.invoke({"input": question}).to_messages()
    expr = llm.invoke(messages).content
    expr = re.sub(r"^```(?:text|plain)?\n|```$", "", expr).strip()
    print(f"[表达式] {expr}")
    value = safe_eval(expr)
    print(f"[结果] {value}")


if __name__ == "__main__":
    main()
