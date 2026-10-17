import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from copilot import (answer_question, detect_services, discovery_brief,
                     recommend_tracks, score_lead, similar_case_studies)
from retrieval import Retriever

R = Retriever()
GOOD = ("We are a clinic with 3 branches. We want an AI chatbot to book appointments, "
        "budget Rs 2 lakh, launch in 2 months. Contact owner@example.com")


def test_retrieval_finds_revio_for_reviews():
    hits = R.search("how does Cynbit manage online reviews and sentiment")
    assert hits and hits[0].id == "prod-03"


def test_answer_cites_sources():
    res = answer_question("who are the founders", R)
    assert res["sources"] and "[" in res["answer"]


def test_unknown_question_is_not_hallucinated():
    res = answer_question("quantum chromodynamics lattice gauge", R)
    assert res["sources"] == []


def test_lead_score_orders_sensibly():
    assert score_lead(GOOD).total > score_lead("need website").total
    assert score_lead(GOOD).tier in {"Warm", "Hot"}


def test_services_and_cases():
    assert detect_services(GOOD)[0][0] == "AI automation"
    assert any(c["client"] == "WizHealth" for c in similar_case_studies(GOOD + " healthcare triage"))


def test_brief_and_tracks():
    assert "Lead tier" in discovery_brief(GOOD, R)["brief"]
    assert recommend_tracks("I want to learn NLP and sentiment with python")[0][0] == "Natural Language Processing"
