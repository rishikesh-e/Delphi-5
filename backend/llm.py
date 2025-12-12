from langchain_groq import ChatGroq
from backend.config import GROQ_API_KEY, MODEL_NAME, TEMPERATURE


def get_llm():
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is missing.")

    llm = ChatGroq(
        groq_api_key=GROQ_API_KEY,
        model_name=MODEL_NAME,
        temperature=TEMPERATURE,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )

    return llm


if __name__ == "__main__":
    try:
        model = get_llm()
        response = model.invoke("Hello, are you ready for a financial debate?")
        print("Groq Connection Successful!")
        print(f"Response: {response.content}")
    except Exception as e:
        print(f"Error connecting to Groq: {e}")