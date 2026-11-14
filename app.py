import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
from src.conversation import ConversationManager

# Page Configuration
st.set_page_config(
    page_title="AmbuPriority & FirstAid AI",
    page_icon="🚑",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom minimal header styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
    }
    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #0b1120 !important;
        border-right: 1px solid #1e293b !important;
    }
    
    /* Floating Assistant Trigger & Chat Styling */
    .chat-box-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
    }
    .msg-user {
        display: flex;
        justify-content: flex-end;
        margin-bottom: 16px;
    }
    .msg-user-content {
        background-color: #2563eb;
        color: #ffffff;
        padding: 10px 16px;
        border-radius: 18px 18px 4px 18px;
        max-width: 80%;
        font-size: 0.95rem;
    }
    .msg-assistant {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        margin-bottom: 20px;
    }
    .msg-assistant-content {
        background-color: #1e293b;
        border: 1px solid #334155;
        color: #e2e8f0;
        padding: 12px 18px;
        border-radius: 18px 18px 18px 4px;
        max-width: 85%;
        font-size: 0.95rem;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conv_manager" not in st.session_state:
    st.session_state.conv_manager = ConversationManager()

# Top Tab Navigation: Portal vs Live FirstAid AI
tabs = st.tabs(["🌐 AmbuPriority Government Portal", "🩺 FirstAid AI Chatbot Assistant", "📄 Portal Documentation"])

PUBLIC_DIR = Path(__file__).resolve().parent / "public"

with tabs[0]:
    index_html_path = PUBLIC_DIR / "index.html"
    if index_html_path.exists():
        with open(index_html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        components.html(html_content, height=1400, scrolling=True)
    else:
        st.error("Portal file index.html not found.")

with tabs[1]:
    st.markdown("### 🩺 FirstAid AI — Instant Emergency Assistant")
    st.caption("Ask questions in **Hinglish, Hindi, or English**. Instant 1-second replies grounded in verified medical guides.")

    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("➕ Clear / New Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    # Message History Container
    for msg in st.session_state.messages:
        role = msg["role"]
        content = msg["content"]
        if role == "user":
            st.markdown(f'<div class="msg-user"><div class="msg-user-content">{content}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="msg-assistant"><span style="font-size:1.5rem;">🩺</span><div class="msg-assistant-content">{content}</div></div>', unsafe_allow_html=True)

    # Chat input
    user_input = st.chat_input("Ask first-aid query (e.g. 'heart attack ke lakshan', 'chot lag gayi kya karu')...")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.markdown(f'<div class="msg-user"><div class="msg-user-content">{user_input}</div></div>', unsafe_allow_html=True)

        history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]]
        with st.chat_message("assistant", avatar="🩺"):
            response_generator = st.session_state.conv_manager.stream_chat(
                user_message=user_input,
                conversation_history=history
            )
            full_response = st.write_stream(response_generator)

        st.session_state.messages.append({"role": "assistant", "content": full_response})
        st.rerun()

with tabs[2]:
    detail_html_path = PUBLIC_DIR / "detail.html"
    if detail_html_path.exists():
        with open(detail_html_path, "r", encoding="utf-8") as f:
            detail_content = f.read()
        components.html(detail_content, height=800, scrolling=True)
