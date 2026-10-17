"""Cynbit Intake Copilot: grounded Q&A, inquiry triage, and BitElevate track matching.

Everything is deterministic and runs offline. An optional LLM step (llm.py) can
polish the discovery brief when an API key is present.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from retrieval import Retriever, load_case_studies

SERVICE_KEYWORDS = {
    "AI automation": ["ai", "chatbot", "llm", "agent", "automate", "automation", "voice", "gpt", "machine learning", "ml", "nlp", "classification", "predict"],
    "Software development": ["app", "website", "web", "mobile", "platform", "saas", "erp", "dashboard", "backend", "api", "portal", "build"],
    "Cloud & infrastructure": ["cloud", "aws", "azure", "migration", "migrate", "devops", "uptime", "deploy", "kubernetes"],
    "Digital marketing": ["seo", "ads", "marketing", "leads", "campaign", "traffic", "social media", "funnel", "crm"],
    "Training / BitElevate": ["intern", "internship", "training", "students", "course", "workshop", "campus", "college"],
}

TRACKS = {
    "Full Stack Development": ["web", "react", "node", "frontend", "backend", "website", "app", "javascript", "full stack"],
    "Artificial Intelligence": ["ai", "chatbot", "llm", "agents", "generative", "gpt", "automation"],
    "Machine Learning": ["machine learning", "ml", "model", "scikit", "prediction", "classification", "regression"],
    "Data Science": ["data science", "statistics", "pandas", "analysis", "hypothesis", "python", "visualization"],
    "Data Analytics": ["analytics", "excel", "sql", "dashboard", "power bi", "tableau", "reporting"],
    "UI/UX Design": ["design", "figma", "ux", "ui", "wireframe", "prototype"],
    "DevOps": ["devops", "docker", "ci/cd", "pipeline", "kubernetes", "linux"],
    "Cloud Computing": ["cloud", "aws", "azure", "serverless", "infrastructure"],
    "Cybersecurity": ["security", "cyber", "pentest", "ethical hacking", "network"],
    "Blockchain Development": ["blockchain", "web3", "solidity", "smart contract", "crypto"],
    "Internet of Things": ["iot", "arduino", "sensors", "embedded", "raspberry"],
    "Deep Learning": ["deep learning", "neural", "pytorch", "tensorflow", "cnn", "computer vision"],
    "Natural Language Processing": ["nlp", "text", "language", "transformer", "sentiment", "bert"],
    "Business Analytics": ["business", "kpi", "strategy", "market", "finance"],
    "Digital Marketing": ["seo", "ads", "marketing", "content", "campaign", "growth"],
    "Social Media Management": ["social media", "instagram", "brand", "community", "reels"],
}


def _tokens(text: str) -> str:
    return " " + re.sub(r"[^a-z0-9+/#. ]", " ", text.lower()) + " "


def _kw_hits(text: str, kws: list[str]) -> int:
    t = _tokens(text)
    return sum(1 for k in kws if f" {k} " in t)


@dataclass
class LeadScore:
    total: int
    breakdown: dict[str, int]
    notes: list[str] = field(default_factory=list)

    @property
    def tier(self) -> str:
        return "Hot" if self.total >= 70 else "Warm" if self.total >= 40 else "Cold"


def score_lead(text: str) -> LeadScore:
    """Transparent rule-based score (0-100). Weights are a starting point to tune on real conversion data."""
    t = text.lower()
    b: dict[str, int] = {}
    notes: list[str] = []

    words = len(t.split())
    b["Specificity of need"] = min(25, words // 4)
    if words < 25:
        notes.append("Short inquiry: ask what problem they want solved.")

    budget = bool(re.search(r"(₹|rs\.?|inr|usd|\$|budget|lakh|lac|\d+k\b)", t))
    b["Budget signal"] = 20 if budget else 0
    if not budget:
        notes.append("No budget signal: ask for a range on the discovery call.")

    timeline = bool(re.search(r"(week|month|deadline|asap|urgent|by (jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)|launch)", t))
    b["Timeline signal"] = 20 if timeline else 0
    if not timeline:
        notes.append("No timeline: ask for target launch date.")

    org = bool(re.search(r"(company|startup|clinic|hospital|store|shop|firm|business|agency|brand|our team|we are|we have)", t))
    b["Real organisation"] = 15 if org else 0

    contact = bool(re.search(r"(@\w+\.\w+|\+?\d[\d\s-]{8,})", t))
    b["Contact provided"] = 10 if contact else 0

    services = sum(1 for kws in SERVICE_KEYWORDS.values() if _kw_hits(t, kws))
    b["Fit with Cynbit services"] = 10 if services else 0
    if not services:
        notes.append("Does not clearly map to a Cynbit service line.")

    return LeadScore(total=min(100, sum(b.values())), breakdown=b, notes=notes)


def detect_services(text: str) -> list[tuple[str, int]]:
    hits = [(s, _kw_hits(text, kws)) for s, kws in SERVICE_KEYWORDS.items()]
    return sorted([h for h in hits if h[1] > 0], key=lambda x: -x[1])


def similar_case_studies(text: str, k: int = 3) -> list[dict]:
    t = _tokens(text)
    scored = []
    for cs in load_case_studies():
        s = sum(2 for tag in cs["tags"] if f" {tag} " in t)
        s += 2 if cs["industry"] in t else 0
        s += 1 if cs["ai"] and _kw_hits(text, SERVICE_KEYWORDS["AI automation"]) else 0
        scored.append((s, cs))
    scored.sort(key=lambda x: -x[0])
    return [dict(cs, match_score=s) for s, cs in scored[:k] if s > 0]


def recommend_tracks(ambition: str, k: int = 3) -> list[tuple[str, int]]:
    scored = [(name, _kw_hits(ambition, kws)) for name, kws in TRACKS.items()]
    scored = [x for x in scored if x[1] > 0]
    return sorted(scored, key=lambda x: -x[1])[:k]


def recommend_duration(ambition: str) -> str:
    t = ambition.lower()
    if any(w in t for w in ["beginner", "new to", "never", "basics", "start from scratch"]):
        return "12 weeks full immersion"
    if any(w in t for w in ["project", "portfolio", "build", "hands-on"]):
        return "8 weeks project-led"
    return "4 weeks intensive"


def answer_question(question: str, retriever: Retriever, k: int = 3) -> dict:
    hits = retriever.search(question, k=k)
    if not hits:
        return {"answer": "I don't have that in the public knowledge base. It may need a discovery call.", "sources": []}
    lines = []
    for h in hits:
        tag = {"verified": "verified", "claimed": "claimed by Cynbit", "inferred": "inference"}.get(h.status, h.status)
        lines.append(f"- {h.text} [{h.id}, {tag}]")
    return {"answer": "\n".join(lines), "sources": [(h.id, h.url, round(h.score, 2)) for h in hits]}


def discovery_brief(inquiry: str, retriever: Retriever) -> dict:
    services = detect_services(inquiry)
    score = score_lead(inquiry)
    cases = similar_case_studies(inquiry)
    svc_hits = retriever.search(", ".join(s for s, _ in services) or inquiry, k=2)
    lines = [
        f"Lead tier: {score.tier} ({score.total}/100)",
        "Likely service lines: " + (", ".join(s for s, _ in services) or "unclear, clarify on call"),
        "Relevant past work: " + ("; ".join(f"{c['client']} ({c['title']})" for c in cases) or "none close"),
        "Questions to ask: " + (" ".join(score.notes) or "Confirm scope, users, integrations and success metric."),
        "Pitch grounding: " + " / ".join(h.id for h in svc_hits),
    ]
    return {"score": score, "services": services, "cases": cases, "brief": "\n".join(lines)}
