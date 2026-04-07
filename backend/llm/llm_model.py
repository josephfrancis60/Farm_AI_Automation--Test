import os
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

# MODEL_NAME = "openai/gpt-oss-120b:free"  # Openrouter
MODEL_NAME = "llama-3.3-70b-versatile"  # GroqCloud

def get_llm():

    llm = ChatGroq(
        model=MODEL_NAME,
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.4 # 0.0 means no creativity and 1.0 means more creativity
    )

    # llm = ChatOpenAI(
    #     model=MODEL_NAME,
    #     openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    #     openai_api_base="https://openrouter.ai/api/v1",
    #     temperature=0.4
    # )

    return llm