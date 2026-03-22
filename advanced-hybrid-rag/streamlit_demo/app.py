"""Streamlit demo placeholder for advanced hybrid RAG."""

import streamlit as st

st.set_page_config(page_title="Advanced Hybrid RAG Demo", layout="wide")


def page_research_assistant() -> None:
	st.title("Research Assistant")
	uploaded = st.file_uploader("Upload paper", type=["pdf", "docx"])
	question = st.text_input("Ask a question")
	if st.button("Run Query") and question:
		st.write("Query submitted:", question)
		st.info("Connect this page to /api/query in next refinement.")
	if uploaded:
		st.success(f"Uploaded: {uploaded.name}")


def page_graph_explorer() -> None:
	st.title("Knowledge Graph Explorer")
	st.write("Graph visualization placeholder. Connect to /api/graph endpoints.")


def page_eval_dashboard() -> None:
	st.title("Evaluation Dashboard")
	st.metric("Faithfulness", 0.0)
	st.metric("Answer Relevancy", 0.0)


def page_config() -> None:
	st.title("System Configuration")
	st.selectbox("Model", ["gpt-4o", "claude-3-5-sonnet", "llama3"])
	st.slider("K vector", 5, 100, 30)
	st.slider("K BM25", 5, 100, 20)
	st.selectbox("Chunk strategy", ["semantic", "recursive", "section", "sliding"])


pages = {
	"Research Assistant": page_research_assistant,
	"Knowledge Graph Explorer": page_graph_explorer,
	"Evaluation Dashboard": page_eval_dashboard,
	"System Configuration": page_config,
}

choice = st.sidebar.radio("Navigate", list(pages.keys()))
pages[choice]()
