from langchain_groq import ChatGroq
from backend.config import GROQ_API_KEY, MODEL_NAME, TEMPERATURE

def get_llm():
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is missing. Please set it in your .env file.")

    try:
        llm = ChatGroq(
            groq_api_key=GROQ_API_KEY,
            model_name=MODEL_NAME,
            temperature=TEMPERATURE,
        )
        return llm
    except Exception as e:
        print(f"Error initializing ChatGroq LLM: {e}")
        raise

if __name__ == "__main__":
    print("Testing llm.py connection to Groq...")
    try:
        model = get_llm()
        response = model.invoke("Please respond with a single word: 'Ready'")
        print("Groq Connection Successful!")
        print(f"Test Response: {response.content}")
    except ValueError as ve:
        print(f"Configuration Error: {ve}")
    except Exception as e:
        print(f"An error occurred during Groq connection test: {e}")