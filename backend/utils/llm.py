from langchain_groq import ChatGroq
from backend.config import config

llm = ChatGroq(model="openai/gpt-oss-20b", api_key=config.GROQ_API_KEY)