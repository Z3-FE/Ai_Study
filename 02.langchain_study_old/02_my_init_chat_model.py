from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from env_utils import (
    API_KEY,
    BASE_URL,
    MODEL_NAME,
    TEMPERATURE  # 导入 float 类型的温度值
)

model = init_chat_model(
    model_name=MODEL_NAME,
    temperature=TEMPERATURE,
    api_key=API_KEY,
    base_url=BASE_URL
)
