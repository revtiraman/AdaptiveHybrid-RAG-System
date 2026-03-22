from __future__ import annotations

# pyright: reportMissingImports=false

import json
from urllib import error, request

import streamlit as st

st.set_page_config(page_title="Adaptive Hybrid RAG Demo", layout="wide")

st.title("Adaptive Hybrid RAG for Scientific Papers")
st.caption("Hybrid retrieval, multi-hop reasoning, and self-verification demo")

api_base = st.sidebar.text_input("API base URL", value="http://127.0.0.1:8000")

st.header("Upload Paper")
with st.form("upload-form"):
    uploaded = st.file_uploader("Select a PDF", type=["pdf"])
    title = st.text_input("Title")
    paper_id = st.text_input("Paper ID (optional)")
    upload_clicked = st.form_submit_button("Upload")

if upload_clicked and uploaded is not None:
    boundary = "----adaptivehybridragboundary"
    file_bytes = uploaded.getvalue()
    parts = []
    for key, value in [("title", title), ("paper_id", paper_id)]:
        if value:
            parts.append(
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"{key}\"\r\n\r\n{value}\r\n".encode("utf-8")
            )

    parts.append(
        (
            f"--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"file\"; filename=\"{uploaded.name}\"\r\n"
            f"Content-Type: application/pdf\r\n\r\n"
        ).encode("utf-8")
    )
    parts.append(file_bytes)
    parts.append(f"\r\n--{boundary}--\r\n".encode("utf-8"))
    payload = b"".join(parts)

    req = request.Request(
        url=f"{api_base}/upload",
        data=payload,
        method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    try:
        with request.urlopen(req, timeout=120) as res:
            response_payload = json.loads(res.read().decode("utf-8"))
        st.success("Upload succeeded")
        st.json(response_payload)
    except error.HTTPError as exc:
        st.error(exc.read().decode("utf-8", errors="replace"))

st.header("Ask a Question")
question = st.text_area("Question", height=120)
section = st.selectbox(
    "Section filter",
    options=["", "abstract", "introduction", "related_work", "method", "experiments", "results", "conclusion"],
)

if st.button("Run Query"):
    payload = {"question": question}
    if section:
        payload["filters"] = {"section": section}

    req = request.Request(
        url=f"{api_base}/query",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with request.urlopen(req, timeout=180) as res:
            result = json.loads(res.read().decode("utf-8"))
        st.subheader("Answer")
        st.write(result.get("answer", ""))
        st.subheader("Claims")
        st.json(result.get("claims", []))
        st.subheader("Diagnostics")
        st.json(result.get("diagnostic", {}))
    except error.HTTPError as exc:
        st.error(exc.read().decode("utf-8", errors="replace"))

st.header("System Stats")
if st.button("Refresh Stats"):
    try:
        with request.urlopen(f"{api_base}/stats", timeout=30) as res:
            st.json(json.loads(res.read().decode("utf-8")))
        with request.urlopen(f"{api_base}/papers", timeout=30) as res:
            st.json(json.loads(res.read().decode("utf-8")))
    except error.HTTPError as exc:
        st.error(exc.read().decode("utf-8", errors="replace"))
