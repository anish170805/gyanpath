from langchain_groq import ChatGroq
from backend.config import config

llm = ChatGroq(model="llama-3.1-8b-instant", api_key=config.GROQ_API_KEY)