import streamlit as st
from rag.memory_store import MemoryStore
from rag.chat_session import ChatSession
from rag.client import chroma_client

st.set_page_config(page_title="Lore Assistant", layout="wide")

# Only build these ONCE per session, not on every rerun
if "chat_session" not in st.session_state:
    lore_store = MemoryStore(chroma_client, name="lore")
    history_store = MemoryStore(chroma_client, name="chat_history")
    st.session_state.chat_session = ChatSession(memory_store=lore_store, history_store=history_store)

session = st.session_state.chat_session

chat_col, lore_col = st.columns([2, 1])

with chat_col:
    st.title("Novel Writing Assistant")

    for turn in session.transcript:
        role = "user" if turn["role"] == "user" else "assistant"
        with st.chat_message(role):
            st.write(turn["parts"][0]["text"])

    user_input = st.chat_input("Say something...")
    if user_input:
        with st.chat_message("user"):
            st.write(user_input)
        with st.chat_message("assistant"):
            reply = session.send(user_input)
            st.write(reply)
        st.rerun()

with lore_col:
    st.subheader("Retrieved this turn")
    st.markdown("**Lore:**")
    st.text(getattr(session, "last_lore_context", "") or "(none)")
    st.markdown("**Past conversation:**")
    st.text(getattr(session, "last_history_context", "") or "(none)")