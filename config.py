from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY")
    EXA_API_KEY: str = os.getenv("EXA_API_KEY")

config = Config()