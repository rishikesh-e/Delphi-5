import os
import shutil
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from backend.config import CHROMA_PERSIST_DIRECTORY, EMBEDDING_MODEL_NAME, CHUNK_SIZE, CHUNK_OVERLAP


def get_embedding_function():
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)


def clear_knowledge_base():
    if os.path.exists(CHROMA_PERSIST_DIRECTORY):
        shutil.rmtree(CHROMA_PERSIST_DIRECTORY)


def add_file_to_knowledge_base(file_path: str):
    if file_path.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    elif file_path.endswith(".txt"):
        loader = TextLoader(file_path)
    else:
        raise ValueError("Unsupported file format. Please upload PDF or TXT.")

    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        is_separator_regex=False,
    )
    chunks = text_splitter.split_documents(documents)

    Chroma.from_documents(
        documents=chunks,
        embedding=get_embedding_function(),
        persist_directory=str(CHROMA_PERSIST_DIRECTORY)
    )

    return f"Successfully processed {len(chunks)} chunks from {os.path.basename(file_path)}."


def query_knowledge_base(query: str, k: int = 3) -> str:
    vector_store = Chroma(
        persist_directory=str(CHROMA_PERSIST_DIRECTORY),
        embedding_function=get_embedding_function()
    )

    results = vector_store.similarity_search(query, k=k)

    context_text = "\n\n---\n\n".join([doc.page_content for doc in results])

    return context_text


if __name__ == "__main__":
    try:
        # clear_knowledge_base()
        # print(add_file_to_knowledge_base("test.txt"))
        # context = query_knowledge_base("What is the financial outlook?")
        # print(context)
        pass
    except Exception as e:
        print(e)