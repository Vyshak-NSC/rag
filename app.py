import streamlit as st

from rag.memory_store import MemoryStore
from rag.chat_session import ChatSession
from rag.client import chroma_client


st.set_page_config(
    page_title="RAG Test",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.sidebar.title("Menu")
st.markdown("""
<style>
.block-container {
    padding-top: 1rem;
    padding-bottom: 0rem;
    padding-left: 1rem;
    padding-right: 1rem;
    max-width: 100%;
}

[data-testid="stVerticalBlock"] {
    margin-left:0;
    padding:0;
}

[data-testid="stChatInput"] {
    border-radius: 12px;
}

[data-testid="stChatInputTextArea"] {
    margin-left: 0;
    padding-right: 1px;
}
</style>
""", unsafe_allow_html=True)

st.title("RAG - Test")
chat_area = st.container(height=400)

if "chat_session" not in st.session_state:
    lore_store = MemoryStore(chroma_client, name="lore")
    history_store = MemoryStore(chroma_client, name="chat_history")
    st.session_state["chat_session"] = ChatSession(memory_store=lore_store, history_store=history_store)
    st.session_state["messages"] = []

with chat_area:
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.write(msg["text"])

user_inp = st.chat_input("Write a message ")

if user_inp:
    with chat_area:
        with st.chat_message('user'):
            st.write(user_inp)
    st.session_state['messages'].append({"role":"user", "text":user_inp})
    
    
    with chat_area:
        with st.chat_message('assistant'):
            with st.spinner("Thinking..."):
                reply = st.session_state['chat_session'].send(user_inp)
            st.write(reply)
    
    st.session_state['messages'].append({"role":"model", "text":reply})
    