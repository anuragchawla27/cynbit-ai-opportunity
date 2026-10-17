"""Train and evaluate the lead classifier. Run: python scripts/train_eval.py"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import joblib  # noqa: E402
import numpy as np  # noqa: E402
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score  # noqa: E402
from sklearn.model_selection import StratifiedKFold  # noqa: E402

from copilot import score_lead  # noqa: E402
from lead_data import generate  # noqa: E402
from lead_model import MODEL_PATH, LeadClassifier  # noqa: E402

LABELS = ["Cold", "Warm", "Hot"]
X, y = generate(1500, seed=7)
y = np.array(y)
hand = json.loads((ROOT / "data" / "leads" / "handwritten_test.json").read_text(encoding="utf-8"))
Xh, yh = [r["text"] for r in hand], np.array([r["label"] for r in hand])


def rules(texts):
    return [score_lead(t).tier for t in texts]


def cv(make):
    f1s = []
    for tr, te in StratifiedKFold(5, shuffle=True, random_state=0).split(X, y):
        Xtr, Xte = [X[i] for i in tr], [X[i] for i in te]
        pred = make(Xtr, y[tr], Xte)
        f1s.append(f1_score(y[te], pred, average="macro"))
    return float(np.mean(f1s)), float(np.std(f1s))


methods = {
    "Rule-based score (baseline)": lambda a, b, c: rules(c),
    "Logistic regression, text only": lambda a, b, c: LeadClassifier(use_signals=False).fit(a, b).predict(c),
    "Logistic regression, text + signals": lambda a, b, c: LeadClassifier().fit(a, b).predict(c),
}

results = {}
for name, fn in methods.items():
    m, s = cv(fn)
    hp = fn(X, y, Xh)
    results[name] = {
        "synthetic_cv_macro_f1": round(m, 3), "synthetic_cv_std": round(s, 3),
        "handwritten_macro_f1": round(float(f1_score(yh, hp, average="macro")), 3),
        "handwritten_accuracy": round(float(accuracy_score(yh, hp)), 3),
        "confusion_handwritten": confusion_matrix(yh, hp, labels=LABELS).tolist(),
    }

final = LeadClassifier().fit(X, y)
MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
joblib.dump(final, MODEL_PATH)
final_pred = final.predict(Xh)
report = classification_report(yh, final_pred, labels=LABELS, zero_division=0)
wrong = [(r["label"], p, r["text"][:90]) for r, p in zip(hand, final_pred) if r["label"] != p]

(ROOT / "reports").mkdir(exist_ok=True)
(ROOT / "reports" / "lead_model_eval.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

lines = ["# Lead classifier evaluation", "",
         "Train: 1,500 synthetic inquiries (seed 7). Held-out: 30 hand-written inquiries (10 per class) written separately from the generator templates.", "",
         "| Method | Synthetic 5-fold macro-F1 | Hand-written macro-F1 | Hand-written accuracy |", "|---|---|---|---|"]
for k, v in results.items():
    lines.append(f"| {k} | {v['synthetic_cv_macro_f1']} +/- {v['synthetic_cv_std']} | {v['handwritten_macro_f1']} | {v['handwritten_accuracy']} |")
lines += ["", "Confusion matrix on hand-written set, final model (rows = true, cols = predicted; order Cold, Warm, Hot):", "",
          "```", str(confusion_matrix(yh, final_pred, labels=LABELS)), "```", "", "```", report, "```", "",
          f"Misclassified hand-written examples ({len(wrong)}):", ""]
lines += [f"- true {t}, predicted {p}: {s}" for t, p, s in wrong]
(ROOT / "reports" / "lead_model_eval.md").write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
