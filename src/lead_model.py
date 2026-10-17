"""Lead-qualification classifier: TF-IDF text features + engineered intent signals -> Cold/Warm/Hot."""
from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import scipy.sparse as sp
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from copilot import score_lead

ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = ROOT / "models" / "lead_model.joblib"
SIGNALS = ["Specificity of need", "Budget signal", "Timeline signal",
           "Real organisation", "Contact provided", "Fit with Cynbit services"]


def signal_matrix(texts: list[str]) -> np.ndarray:
    return np.array([[score_lead(t).breakdown[k] for k in SIGNALS] for t in texts], dtype=float)


class LeadClassifier:
    def __init__(self, use_signals: bool = True, C: float = 2.0):
        self.use_signals = use_signals
        self.C = C
        self.tfidf = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)
        self.scaler = StandardScaler()
        self.clf = LogisticRegression(C=C, max_iter=2000, class_weight="balanced")

    def _features(self, texts: list[str], fit: bool = False):
        X = self.tfidf.fit_transform(texts) if fit else self.tfidf.transform(texts)
        if not self.use_signals:
            return X
        S = signal_matrix(texts)
        S = self.scaler.fit_transform(S) if fit else self.scaler.transform(S)
        return sp.hstack([X, sp.csr_matrix(S)]).tocsr()

    def fit(self, texts: list[str], y: list[str]) -> "LeadClassifier":
        self.clf.fit(self._features(texts, fit=True), y)
        return self

    def predict(self, texts: list[str]) -> list[str]:
        return list(self.clf.predict(self._features(texts)))

    def predict_proba(self, texts: list[str]) -> list[dict[str, float]]:
        P = self.clf.predict_proba(self._features(texts))
        return [dict(zip(self.clf.classes_, row)) for row in P]


def get_model() -> LeadClassifier:
    """Load the trained model, training it on synthetic data first if no saved model exists."""
    if MODEL_PATH.exists():
        return joblib.load(MODEL_PATH)
    from lead_data import generate

    X, y = generate()
    model = LeadClassifier().fit(X, y)
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    return model
