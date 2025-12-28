"""
Stuff：把多份文档直接拼接成单一上下文后交给模型一次性回答。
Stuff：文档少、内容短、答案直接；追求简单、低开销。
"""
import os
import sqlite3
import re
from pathlib import Path

from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains.sql_database.query import create_sql_query_chain
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from langchain_study.env_utils import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL_NAME_RE, DEEPSEEK_TEMPERATURE

# 演示：使用 create_sql_query_chain 生成 SQL，并执行返回结果
# 步骤概览：
# 1) 创建本地 SQLite 演示数据库
# 2) 初始化 LLM（DeepSeek 的 OpenAI 兼容接口）
# 3) 构造 PromptTemplate（包含 input/table_info/top_k）
# 4) 创建 SQL 生成链 create_sql_query_chain
# 5) 生成原始输出（可能含有 ```sql 代码块）
# 6) 清洗为纯 SQL 文本
# 7) 执行 SQL 并输出结果反馈

def _clean_sql(text: str) -> str:
    if not isinstance(text, str):
        return str(text)
    m = re.search(r"```(?:sql)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if m:
        text = m.group(1)
    text = re.sub(r"^SQLQuery:\s*", "", text, flags=re.IGNORECASE)
    text = text.strip()
    return text

def format_result(res) -> str:
    # 将常见的查询结果格式化为更易读的中文说明
    try:
        if isinstance(res, list):
            if len(res) == 0:
                return "空结果集"
            first = res[0]
            if isinstance(first, (tuple, list)) and len(first) == 1:
                return f"标量结果: {first[0]}"
            return f"行数: {len(res)}，示例首行: {first}"
        return str(res)
    except Exception:
        return repr(res)

def _ensure_demo_db() -> str:
    # 创建用于演示的本地 SQLite 数据库，并返回 SQLAlchemy 连接 URI（sqlite:///...）
    base = Path(__file__).parent / "data"  # 数据文件目录：与当前脚本同级的 data 子目录
    base.mkdir(parents=True, exist_ok=True)  # 确保目录存在
    db_path = base / "sql_chain_demo.db"  # 数据库文件路径

    conn = sqlite3.connect(str(db_path))  # 连接到 SQLite 数据库（若不存在则创建）
    cur = conn.cursor()

    # 创建示例表 employees（若不存在），包含 id/name/department 三列
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            department TEXT NOT NULL
        )
        """
    )

    # 检查是否已有数据；若为空则插入若干演示数据
    cur.execute("SELECT COUNT(1) FROM employees")
    count = cur.fetchone()[0]
    if count == 0:
        cur.executemany(
            "INSERT INTO employees (name, department) VALUES (?, ?)",
            [
                ("Alice", "Engineering"),
                ("Bob", "Engineering"),
                ("Carol", "HR"),
                ("Dave", "Finance"),
                ("Eve", "Engineering"),
                ("Frank", "Sales"),
                ("Grace", "Sales"),
            ],
        )

    conn.commit()  # 提交事务，持久化建表与插入操作
    conn.close()  # 关闭连接

    # 返回 SQLAlchemy 使用的 URI 格式；Windows 路径中的反斜杠替换为正斜杠
    return "sqlite:///" + str(db_path).replace("\\", "/")


def main():
    # [步骤1] 创建或准备演示数据库连接
    os.environ["OPENAI_API_KEY"] = DEEPSEEK_API_KEY
    os.environ["OPENAI_BASE_URL"] = DEEPSEEK_BASE_URL


    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("请设置环境变量 OPENAI_API_KEY")
    uri = _ensure_demo_db()
    db = SQLDatabase.from_uri(uri)
    print(f"[步骤1] 数据库URI: {uri}")
    print(f"[步骤1] 可用表: {db.get_usable_table_names()}")

    # 1. 初始化 LLM 和 Parser
    # [步骤2] 初始化LLM
    llm = ChatOpenAI(
        model=DEEPSEEK_MODEL_NAME_RE,  # 使用 model 而非 model_name
        temperature=DEEPSEEK_TEMPERATURE,
    )
    print(f"[步骤2] 使用模型: {DEEPSEEK_MODEL_NAME_RE}, temperature={DEEPSEEK_TEMPERATURE}")
    # [步骤3] 构造 PromptTemplate（必须包含 input/table_info/top_k）
    prompt = PromptTemplate.from_template(
        """
        你是SQLite专家。根据给出的数据库架构生成回答问题的SQL查询。
        只返回纯SQL，不要任何解释或标记。
        仅考虑前{top_k}个相关表。
        可用表信息：
        {table_info}
        问题：{input}
        """
    )
    print(f"[步骤3] Prompt输入变量: {getattr(prompt, 'input_variables', None)}")
    # [步骤4] 创建 SQL 生成链
    # chain = create_sql_query_chain(llm=llm, db=db, prompt=prompt)  # prompt可选项
    chain = create_sql_query_chain(llm=llm, db=db)  # prompt可选项
    print("[步骤4] SQL 生成链已创建")
    question = "有多少员工？"
    print(f"[步骤5] 问题: {question}")
    """
    top_k:小型数据库或问题明确： top_k 设为 3~5 。 表很多或问题涉及多实体：提高到 8~12 ，或分问题多次调用。
    table_names_to_use: 如果需要组合多表，按需要加入到 table_names_to_use ，并适当增大 top_k
    """
    sql = chain.invoke({"question": question, "top_k": 5, "table_names_to_use":["employees"]})
    print(f"[步骤5] 原始输出: {repr(sql)}")

    # [步骤6] 清洗为纯 SQL
    cleaned = _clean_sql(sql)
    print(f"[步骤6] 纯SQL: {cleaned}")

    # [步骤7] 执行 SQL 并返回结果反馈
    try:
        result = db.run(cleaned)
        print(f"[步骤7] 执行成功，原始结果: {repr(result)}")
        print(f"[步骤7] 结果反馈: {format_result(result)}")
    except Exception as e:
        print(f"[步骤7] 执行失败: {e}")


if __name__ == "__main__":
    main()




