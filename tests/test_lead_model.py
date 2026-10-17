import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from lead_data import generate
from lead_model import LeadClassifier


def test_generator_is_deterministic_and_balanced_enough():
    a = generate(300, seed=1)
    assert a == generate(300, seed=1)
    assert {"Cold", "Warm", "Hot"} <= set(a[1])


def test_classifier_separates_extremes():
    X, y = generate(1200, seed=7)
    m = LeadClassifier().fit(X, y)
    hot = ("We are a 5-branch clinic. We want an AI chatbot for bookings. Budget is around Rs 3 lakh. "
           "Need it live in 6 weeks. Call me on 9876543210.")
    p = m.predict([hot, "hi"])
    assert p == ["Hot", "Cold"]
    probs = m.predict_proba([hot])[0]
    assert abs(sum(probs.values()) - 1) < 1e-6
