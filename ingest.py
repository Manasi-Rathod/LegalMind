import os
import logging
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# ----------------------------- LOGGING -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)

# ----------------------------- EMBEDDING MODEL -----------------------------
def load_embeddings():
    try:
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )
        logging.info("📦 Embeddings successfully loaded!")
        return embeddings
    except Exception as e:
        logging.error(f"❌ Error loading embeddings: {e}")
        raise e

# ----------------------------- LOAD DOCUMENTS -----------------------------
def load_documents(pdf_files):
    all_docs = []
    for file in pdf_files:
        if not os.path.exists(file):
            logging.warning(f"⚠ File not found: {file}")
            continue

        try:
            logging.info(f"📥 Loading PDF: {file}")
            loader = PyPDFLoader(file)
            docs = loader.load()
            all_docs.extend(docs)
        except Exception as e:
            logging.error(f"❌ Error loading {file}: {e}")

    logging.info(f"📦 Total pages loaded: {len(all_docs)}")
    return all_docs

# ----------------------------- SPLIT INTO CHUNKS -----------------------------
def chunk_documents(docs):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = splitter.split_documents(docs)
    logging.info(f"✂ Total chunks created: {len(chunks)}")
    return chunks

# ----------------------------- STORE IN CHROMA DB -----------------------------
def store_embeddings(chunks, embeddings):
    try:
        vector_store = Chroma(
            persist_directory="chroma_db_legal_bot_part1",
            embedding_function=embeddings
        )
        vector_store.add_documents(chunks)
        vector_store.persist()
        logging.info("🚀 Embeddings successfully stored in Chroma DB!")
    except Exception as e:
        logging.error(f"❌ Error storing embeddings: {e}")
        raise e

# ----------------------------- MAIN FUNCTION -----------------------------
def main():
    logging.info("🔍 Starting ingestion process...")

    # Define PDF files inside function to avoid NameError
    PDF_FILES = [
        "docs/Constitution_of_India.pdf",
        "docs/CrPC.pdf",
        "docs/IPC_1860.pdf"
    ]

    embeddings = load_embeddings()
    documents = load_documents(PDF_FILES)

    if not documents:
        logging.error("❌ No documents loaded. Exiting.")
        return

    chunks = chunk_documents(documents)
    store_embeddings(chunks, embeddings)

    logging.info("🎉 Ingestion completed successfully!")

# ----------------------------- RUN SCRIPT -----------------------------
if __name__ == "__main__":
    main()
