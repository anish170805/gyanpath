from langchain_groq import ChatGroq
from config import config

llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=config.GROQ_API_KEY)