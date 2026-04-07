from langchain_groq import ChatGroq
from backend.config import config

llm = ChatGroq(model="meta-llama/llama-4-scout-17b-16e-instruct", api_key=config.GROQ_API_KEY)