import requests
import streamlit as st

API_BASE = "http://127.0.0.1:8000/api/v1"

st.set_page_config(page_title="Vietnamese Summarization", page_icon="📝", layout="centered")
st.title("Vietnamese Text Summarization")
st.caption("Skeleton UI - Phase 1")

with st.sidebar:
    st.subheader("Backend Status")
    if st.button("Check Health"):
        try:
            health = requests.get(f"{API_BASE}/health", timeout=10)
            health.raise_for_status()
            st.success(f"API: {health.json().get('status', 'unknown')}")
        except Exception as exc:
            st.error(f"Cannot connect backend: {exc}")

input_text = st.text_area("Input text", height=220, placeholder="Paste Vietnamese text here...")
max_sentences = st.slider("Max summary sentences", min_value=1, max_value=10, value=3)
engine = st.selectbox(
    "Engine",
    options=["tfidf", "textrank"],
    index=0,
    help="Choose extractive engine used by backend.",
)

if st.button("Summarize"):
    try:
        response = requests.post(
            f"{API_BASE}/summarize",
            json={"text": input_text, "max_sentences": max_sentences, "engine": engine},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        st.subheader("Summary")
        st.write(data.get("summary", ""))
        st.subheader("Metadata")
        st.json(data.get("metadata", {}))
    except Exception as exc:
        st.error(f"Summarize failed: {exc}")
