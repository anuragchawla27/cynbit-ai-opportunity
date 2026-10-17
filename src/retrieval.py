"""Knowledge-base loading and TF-IDF retrieval (no API key or network needed)."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

KB_DIR = Path(__file__).resolve().parent.parent / "data" / "kb"


@dataclass
class Hit:
    id: str
    score: float
    status: str
    url: str
    text: str


def load_chunks(kb_dir: Path = KB_DIR) -> list[dict]:
    with open(kb_dir / "cynbit_kb.json", encoding="utf-8") as f:
        return json.load(f)["chunks"]


def load_case_studies(kb_dir: Path = KB_DIR) -> list[dict]:
    with open(kb_dir / "case_studies.json", encoding="utf-8") as f:
        return json.load(f)


class Retriever:
    def __init__(self, chunks: list[dict] | None = None):
        self.chunks = chunks or load_chunks()
        self.vectorizer = TfidfVectorizer(
            stop_words="english", ngram_range=(1, 2), sublinear_tf=True
        )
        self.matrix = self.vectorizer.fit_transform(c["text"] for c in self.chunks)

    def search(self, query: str, k: int = 3, min_score: float = 0.05) -> list[Hit]:
        if not query.strip():
            return []
        sims = cosine_similarity(self.vectorizer.transform([query]), self.matrix)[0]
        order = sims.argsort()[::-1][:k]
        return [
            Hit(
                id=self.chunks[i]["id"],
                score=float(sims[i]),
                status=self.chunks[i]["status"],
                url=self.chunks[i]["url"],
                text=self.chunks[i]["text"],
            )
            for i in order
            if sims[i] >= min_score
        ]
