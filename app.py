import os
import streamlit as st
import uuid
from dotenv import load_dotenv
from lawglance_main import Lawglance
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from groq import Groq

# ======================
# PAGE CONFIG
# ======================
st.set_page_config(
    page_title="LawGlance – AI Legal Assistant",
    page_icon="⚖️",
    layout="wide"
)

load_dotenv()

# ======================
# CUSTOM PREMIUM CSS
# ======================
st.markdown("""
<style>
body { font-family: 'Inter', sans-serif; }

.hero { text-align: center; padding-top: 40px; }
.hero-title {
    font-size: 58px;
    font-weight: 800;
    background: linear-gradient(90deg, #7b2ff7, #f107a3);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.hero-sub { font-size: 19px; color: #555; }

.custom-btn {
    padding: 14px 26px;
    background: linear-gradient(45deg, #845ef7, #b05ef7);
    color: white !important;
    border-radius: 10px;
    text-decoration: none !important;
    font-size: 17px;
    transition: all 0.3s ease;
}
.custom-btn:hover { transform: scale(1.05); }

.feature-card {
    background: white;
    padding: 30px;
    border-radius: 14px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    text-align: center;
    transition: all 0.3s ease;
}
.feature-card:hover { transform: translateY(-4px); }

.chat-box {
    background: white;
    padding: 20px;
    border-radius: 14px;
    border: 1px solid #e0e0e0;
    box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    white-space: pre-line; /* PRESERVE LINE BREAKS */
    font-size: 16px;
}

.chat-user {
    background: #e9e3ff;
    padding: 12px;
    border-radius: 12px;
    margin-bottom: 10px;
}
.chat-bot {
    background: #f5f3ff;
    padding: 12px;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

# ======================
# HERO SECTION
# ======================
st.markdown("""
<div class="hero">
    <div class="hero-title">LawGlance</div>
    <p class="hero-sub">Your AI Legal Assistant Powered by RAG</p>
    <p>Instant, accurate answers to complex legal questions.</p>
    <a href="#chat" class="custom-btn">Start Chatting</a>
</div>
""", unsafe_allow_html=True)

st.markdown("## Why Choose LawGlance?")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown('<div class="feature-card">⚖️<br><div class="feature-title">Legal Precision</div>Based only on IPC, CrPC, Constitution, etc.</div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="feature-card">⚡<br><div class="feature-title">Fast Response</div>Instant legal answers.</div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="feature-card">🔒<br><div class="feature-title">Secure</div>Your data stays private.</div>', unsafe_allow_html=True)

st.markdown("---")
st.markdown('<a id="chat"></a>', unsafe_allow_html=True)
st.markdown("### 💬 Try LawGlance Now")

# ======================
# SESSION
# ======================
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

thread_id = st.session_state.thread_id

# ======================
# GROQ LLM SETUP
# ======================
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    st.error("⚠️ Missing GROQ_API_KEY in .env")
    st.stop()

try:
    client = Groq(api_key=groq_api_key)

    class SimpleGroqLLM:
        def __call__(self, prompt):
            try:
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2
                )
                return response.choices[0].message.content
            except Exception as e:
                return f"⚠️ LLM Error: {e}"

    llm = SimpleGroqLLM()
    st.success("🚀 Groq LLM Loaded")
except Exception as e:
    st.error(f"❌ Error loading Groq: {e}")
    st.stop()

# ======================
# EMBEDDINGS
# ======================
try:
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )
    st.success("📦 Embeddings Loaded (CPU Safe)")
except Exception as e:
    st.error(f"Embedding error: {e}")
    st.stop()

# ======================
# CHROMA DB
# ======================
try:
    vector_store = Chroma(
        persist_directory="chroma_db_legal_bot_part1",
        embedding_function=embeddings
    )
    st.success("📚 Legal docs loaded")
except Exception as e:
    st.error(f"Vector Store Error: {e}")
    st.stop()

# ======================
# LAWGLANCE CORE
# ======================
law = Lawglance(llm, embeddings, vector_store)

# ======================
# CHAT
# ======================
prompt = st.text_input("Ask any legal question...", key="user_input")

if prompt:
    with st.spinner("📌 Analyzing legal query..."):
        try:
            result, chat_history = law.conversational(prompt, thread_id)
            clean_result = (
                result.replace("**", "")
                      .replace("<b>", "")
                      .replace("</b>", "")
                      .strip()
            )

            st.markdown(f"""
            <div class="chat-box">
                <div class="chat-user"><b>🧑‍⚖️ You:</b> {prompt}</div>
                <div class="chat-bot"><b>🤖 LawGlance:</b><br>{clean_result}</div>
            </div>
            """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"⚠️ Error: {e}")
