"""Streamlit chat and human-feedback interface."""

import os
import sys
import uuid
from pathlib import Path
from typing import Any

# Streamlit Community Cloud executes this file from the repository root but
# places the entrypoint directory first on sys.path.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st

try:
    streamlit_secrets = st.secrets.to_dict()
except FileNotFoundError:
    # Local development uses the root .env file; Streamlit Community Cloud
    # supplies these values through secrets.toml.
    streamlit_secrets = {}

for secret_name in ("TELCORAG_BACKEND_URL", "TELCORAG_ADMIN_PASSWORD"):
    if secret_name in streamlit_secrets and secret_name not in os.environ:
        os.environ[secret_name] = str(streamlit_secrets[secret_name])

from tool.frontend.api_client import BackendError, ask, fetch_stats, submit_rating
from tool.settings import RETRIEVER_NAME, SETTINGS


st.set_page_config(page_title="TelcoRAG Feedback", page_icon="💬", layout="wide")
st.markdown(
    """
    <style>
      .block-container {max-width: 1120px; padding-top: 1.6rem;}
      [data-testid="stChatMessage"] {border: 1px solid rgba(128,128,128,.16); border-radius: 16px;}
      .source-meta {font-size:.82rem; opacity:.72; margin-bottom:.5rem;}
      .source-text {line-height:1.55;}
      .rating-help {font-size:.82rem; opacity:.72;}
    </style>
    """,
    unsafe_allow_html=True,
)


def init_state() -> None:
    st.session_state.setdefault("session_id", uuid.uuid4().hex)
    st.session_state.setdefault("rater_id", uuid.uuid4().hex)
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("submitted_ratings", {})


def source_title(source: dict[str, Any]) -> str:
    location = [source.get("document", "Unknown")]
    if source.get("chapter"):
        location.append(source["chapter"])
    if source.get("section"):
        location.append(source["section"])
    if source.get("subsection_id") not in (None, "", "N/A"):
        location.append(f"§ {source['subsection_id']}")
    score = source.get("score")
    suffix = f" · score {score:.3f}" if isinstance(score, (float, int)) else ""
    return f"{source.get('rank', '–')}. {' › '.join(location)}{suffix}"


def render_sources(sources: list[dict[str, Any]], response_id: str) -> None:
    with st.expander(f"Retrieved subsections ({len(sources)})", expanded=False):
        if not sources:
            st.info("No subsections were retrieved for this answer.")
        for source in sources:
            st.markdown(f"**{source_title(source)}**")
            pages = source.get("page_numbers")
            if pages:
                st.caption(f"Pages: {pages}")
            st.markdown(source.get("text") or "_No subsection text._")
            if source is not sources[-1]:
                st.divider()


def rating_popover(message: dict[str, Any]) -> None:
    response_id = message["response_id"]
    previous = st.session_state.submitted_ratings.get(response_id, {})
    label = "Edit rating" if previous else "Rate this response"
    with st.popover(label, use_container_width=False):
        st.caption("Score each criterion from 1 (poor) to 5 (excellent).")
        with st.form(f"rating_{response_id}"):
            relevance = st.select_slider(
                "Retrieval relevance",
                options=[1, 2, 3, 4, 5],
                value=previous.get("retrieval_relevance", 3),
                help="How relevant were the retrieved subsections to the question?",
            )
            completeness = st.select_slider(
                "Completeness",
                options=[1, 2, 3, 4, 5],
                value=previous.get("completeness", 3),
                help="Did the answer cover all important parts of the question?",
            )
            correctness = st.select_slider(
                "Correctness",
                options=[1, 2, 3, 4, 5],
                value=previous.get("correctness", 3),
                help="Was the answer accurate and supported by the retrieved material?",
            )
            comment = st.text_area(
                "Comment (optional)",
                value=previous.get("comment", ""),
                max_chars=5000,
                placeholder="What worked well, or what should be improved?",
            )
            submitted = st.form_submit_button("Save rating", type="primary")
        if submitted:
            payload = {
                "rater_id": st.session_state.rater_id,
                "retrieval_relevance": relevance,
                "completeness": completeness,
                "correctness": correctness,
                "comment": comment,
            }
            try:
                result = submit_rating(response_id, payload)
            except BackendError as exc:
                st.error(str(exc))
            else:
                st.session_state.submitted_ratings[response_id] = payload
                verb = "updated" if result.get("updated") else "saved"
                st.success(f"Rating {verb}. Thank you.")


def render_assistant_message(message: dict[str, Any]) -> None:
    with st.chat_message("assistant"):
        st.markdown(message["answer"])
        st.caption(
            f"{message.get('retriever', RETRIEVER_NAME)} retriever · "
            f"{message.get('latency_ms', 0) / 1000:.1f}s"
        )
        render_sources(message.get("retrieved_subsections", []), message["response_id"])
        rating_popover(message)


def chat_page() -> None:
    st.title("Ask TelcoRAG")
    st.caption(
        "Ask a question, inspect every retrieved subsection, then rate the answer. "
        f"Active retriever: `{RETRIEVER_NAME}`."
    )

    for message in st.session_state.messages:
        if message["role"] == "user":
            with st.chat_message("user"):
                st.markdown(message["content"])
        else:
            render_assistant_message(message)

    question = st.chat_input("Ask a question about the telecom knowledge base…")
    if not question:
        return

    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        with st.spinner("Retrieving subsections and generating an answer…"):
            try:
                result = ask(question, st.session_state.session_id)
            except BackendError as exc:
                st.error(str(exc))
                return
    message = {"role": "assistant", **result}
    st.session_state.messages.append(message)
    st.rerun()


def admin_page() -> None:
    st.title("Rating analytics")
    st.caption("Aggregate human feedback and recent reviewer comments.")
    password = st.text_input(
        "Admin password",
        type="password",
        help="Leave blank when TELCORAG_ADMIN_PASSWORD is not configured.",
    )
    if SETTINGS.admin_password and not password:
        st.info("Enter the admin password to load the dashboard.")
        return
    try:
        stats = fetch_stats(password)
    except BackendError as exc:
        st.error(str(exc))
        return

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Responses", stats["total_responses"])
    m2.metric("Rated responses", stats["rated_responses"])
    m3.metric("Ratings", stats["total_ratings"])
    m4.metric("Rating coverage", f"{stats['rating_coverage_percent']:.1f}%")

    st.subheader("Average scores")
    criteria = stats["criteria"]
    columns = st.columns(3)
    for column, (name, values) in zip(columns, criteria.items()):
        column.metric(name, f"{values['average']:.2f} / 5", f"n = {values['count']}")

    st.subheader("Score distributions")
    distribution = pd.DataFrame(
        {name: values["distribution"] for name, values in criteria.items()}
    )
    distribution.index.name = "Score"
    st.bar_chart(distribution)

    st.subheader("Retriever comparison")
    breakdown = pd.DataFrame(stats["retriever_breakdown"])
    if breakdown.empty:
        st.info("No response data yet.")
    else:
        st.dataframe(breakdown, use_container_width=True, hide_index=True)

    st.subheader("Recent feedback")
    feedback = stats["recent_feedback"]
    if not feedback:
        st.info("No ratings have been submitted yet.")
    for item in feedback:
        summary = (
            f"{item['question'][:90]} · relevance {item['retrieval_relevance']}/5 · "
            f"completeness {item['completeness']}/5 · correctness {item['correctness']}/5"
        )
        with st.expander(summary):
            st.caption(f"{item['created_at']} · {item['retriever']} · {item['response_id']}")
            st.markdown("**Question**")
            st.write(item["question"])
            st.markdown("**Answer**")
            st.write(item["answer"])
            st.markdown("**Reviewer comment**")
            st.write(item["comment"] or "_No comment._")


init_state()
with st.sidebar:
    st.header("TelcoRAG")
    page = st.radio("Workspace", ["Chat", "Admin analytics"])
    st.caption(f"Retriever: {RETRIEVER_NAME}")
    if page == "Chat" and st.button("New conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = uuid.uuid4().hex
        st.rerun()

if page == "Chat":
    chat_page()
else:
    admin_page()
