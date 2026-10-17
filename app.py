"""Cynbit Intake Copilot (Streamlit). Run: streamlit run app.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import streamlit as st  # noqa: E402

from copilot import (  # noqa: E402
    answer_question,
    discovery_brief,
    recommend_duration,
    recommend_tracks,
)
from lead_model import get_model  # noqa: E402
from retrieval import Retriever  # noqa: E402

st.set_page_config(page_title="Cynbit Intake Copilot", page_icon="🧭", layout="wide")


@st.cache_resource
def get_retriever() -> Retriever:
    return Retriever()


retriever = get_retriever()
st.title("Cynbit Intake Copilot")
st.caption("Proof of concept: a grounded assistant for Cynbit's sales inquiries and BitElevate applicants. Offline by default; every answer cites its source chunk.")

tab1, tab2, tab3 = st.tabs(["Ask Cynbit", "Triage a client inquiry", "BitElevate track match"])

with tab1:
    q = st.text_input("Ask about Cynbit (services, products, clients, team, hiring)", "What AI services does Cynbit offer?")
    if q:
        res = answer_question(q, retriever)
        st.markdown(res["answer"])
        for cid, url, score in res["sources"]:
            st.caption(f"{cid} · relevance {score} · {url}")

with tab2:
    sample = "We are a 3-branch dental clinic in Jaipur. We want an AI chatbot on WhatsApp to book appointments and answer patient queries, budget around Rs 2 lakh, launch within 2 months. Contact: owner@example.com"
    inquiry = st.text_area("Paste an inbound inquiry", sample, height=140)
    if st.button("Analyse inquiry"):
        r = discovery_brief(inquiry, retriever)
        c1, c2 = st.columns(2)
        c1.metric("Lead score", f"{r['score'].total}/100", r["score"].tier)
        c1.json(r["score"].breakdown)
        probs = get_model().predict_proba([inquiry])[0]
        c1.write("ML classifier: " + ", ".join(f"{k} {v:.0%}" for k, v in sorted(probs.items(), key=lambda kv: -kv[1])))
        c2.subheader("Similar past work")
        for cs in r["cases"] or []:
            c2.write(f"**{cs['client']}**: {cs['title']}")
        if not r["cases"]:
            c2.write("No close case study. Flag as new territory.")
        st.subheader("Discovery-call brief")
        st.code(r["brief"])

with tab3:
    amb = st.text_area("Applicant ambitions", "I am a final-year student, new to AI, want to build chatbots and a portfolio project with Python and NLP.", height=100)
    if st.button("Recommend track"):
        recs = recommend_tracks(amb)
        for name, s in recs:
            st.write(f"**{name}** (match strength {s})")
        if not recs:
            st.write("No clear match. Suggest a counselling call.")
        st.write(f"Suggested duration: **{recommend_duration(amb)}**")
