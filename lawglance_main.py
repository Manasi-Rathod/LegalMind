import threading
import logging
from langchain.schema import HumanMessage, AIMessage
from prompts import SYSTEM_PROMPT, QA_PROMPT

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)

class Lawglance:
    """
    LawGlance – Core logic (no Redis)
    Works with Groq LLM + Chroma Vector DB + Local Embeddings
    """

    store = {}  # ⬅ Session-based chat history
    store_lock = threading.Lock()

    def __init__(self, llm, embeddings, vector_store):
        self.llm = llm
        self.embeddings = embeddings
        self.vector_store = vector_store

    def get_session_history(self, session_id):
        """Fetch session chat history or create new session."""
        with Lawglance.store_lock:
            if session_id not in Lawglance.store:
                Lawglance.store[session_id] = []
        return Lawglance.store[session_id]

    def conversational(self, query, session_id):
        logging.info(f"🔍 Incoming query: {query}")

        # Load or create session history
        history = self.get_session_history(session_id)

        # 🔎 RAG Retrieval
        try:
            docs = self.vector_store.similarity_search(query, k=3)
            context = "\n\n".join([d.page_content for d in docs]) if docs else "No relevant legal context found."
        except Exception as e:
            logging.error(f"❌ Vector retrieval failed: {e}")
            context = "Error fetching legal documents."

        # 🧠 Build prompt using structured format
        final_prompt = f"""
{SYSTEM_PROMPT}

📚 Relevant Legal Context:
{context}

{QA_PROMPT}

🧑‍⚖️ Question:
{query}
"""

        # 🗣 Generate response using LLM
        try:
            answer = self.llm(final_prompt)
        except Exception as e:
            answer = f"⚠️ LLM Error: {e}"

        # 💾 Update history
        history.append({"role": "user", "content": query})
        history.append({"role": "assistant", "content": answer})

        return answer, history
