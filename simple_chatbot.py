"""Thius class uses locael model to create embedding and chatgpt api as the llm"""
import os
from dotenv import load_dotenv, find_dotenv

# LangChain core
from langchain.indexes import VectorstoreIndexCreator

# Data loading & vector store
from langchain_community.document_loaders import CSVLoader
from langchain_community.vectorstores import DocArrayInMemorySearch
from langchain_community.embeddings import HuggingFaceEmbeddings  # FREE, local

# Chat model (OpenAI, only used for final answer)
from langchain_openai import ChatOpenAI


def build_index(csv_path: str, csv_encoding: str = "utf-8"):
    """Load data, create embeddings, and build the vector index (one-time)."""
    loader = CSVLoader(file_path=csv_path, encoding=csv_encoding)
    embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    index = VectorstoreIndexCreator(
        vectorstore_cls=DocArrayInMemorySearch,
        embedding=embedding,
        # text_splitter=...  # add if your CSV rows are long
    ).from_loaders([loader])
    return index


def main():
    # ---- Load env ----
    _ = load_dotenv(find_dotenv())

    if not os.getenv("OPENAI_API_KEY"):
        print("WARNING: OPENAI_API_KEY not found in environment. Set it in your .env.")
        # Embedding/indexing runs locally, but chat calls will fail.

    # ---- Config ----
    CSV_PATH = "processed_data.csv"       # your file
    CSV_ENCODING = "utf-8"                # try "utf-8-sig" or "latin-1" if needed
    CHAT_MODEL = "gpt-4o-mini"            # inexpensive and fast; or "gpt-4o"
    TEMPERATURE = 0.0

    # ---- One-time: build index ----
    print("Building embeddings & index (one-time)...")
    index = build_index(CSV_PATH, CSV_ENCODING)
    print("Index ready. Ask me anything about the CSV.")
    print("Type 'exit' or press Enter on a blank line to quit.\n")

    # ---- One-time: init LLM ----
    llm = ChatOpenAI(model=CHAT_MODEL, temperature=TEMPERATURE)

    # ---- Interactive query loop ----
    try:
        while True:
            try:
                query = input("Query> ").strip()
            except EOFError:
                # e.g., Ctrl+D
                print("\nBye!")
                break

            if not query or query.lower() in {"exit", "quit", "q"}:
                print("Bye!")
                break

            # You can also use: index.query_with_sources(query, llm=llm)
            answer = index.query(query, llm=llm)
            print("\n=== Answer ===")
            print(answer)
            print()
    except KeyboardInterrupt:
        print("\nInterrupted. Bye!")


if __name__ == "__main__":
    main()
