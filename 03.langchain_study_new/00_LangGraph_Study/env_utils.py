import os
from dotenv import load_dotenv
from langsmith import expect

# 1. 加载 .env 文件
# load_dotenv() 会自动查找并加载项目根目录下的 .env 文件
load_dotenv()

# 2. 从环境变量中读取 DeepSeek 配置
# os.environ['KEY_NAME'] 或 os.getenv('KEY_NAME')
# 注意：读取到的所有值都是字符串 (str) 类型

API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")

# 读取其他配置并进行类型转换
MODEL_NAME = os.getenv("MODEL_NAME")  # 普通
MODEL_NAME_36 = os.getenv("MODEL_NAME_36")  # 深度思考
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-v1")
# 环境变量读取的是字符串，需要手动转换为需要的类型 (例如 int 或 float)
DEEPSEEK_TEMPERATURE_STR = os.getenv("TEMPERATURE", "0.0")  # 提供默认值防止 None
TEMPERATURE = float(DEEPSEEK_TEMPERATURE_STR)

# ----------------------------------------------------
# 3. 验证和使用配置
# ----------------------------------------------------

print("--- 模型配置信息 ---")
print(f"API Key (前5位): {API_KEY[:5]}...")  # 安全展示
print(f"Base URL: {BASE_URL}")
print(f"TEMPERATURE (float): {TEMPERATURE}")

# 示例：如何将其用于实际的 API 调用
# (这里仅为演示，实际调用需要  SDK 或 requests 库)
if API_KEY and BASE_URL:
    print("\n配置成功，可以开始调用 API。")
else:
    print("\n错误：API Key 或 URL 未设置。请检查 .env 文件。")

if __name__ == "__main__":
    print('主文件')
