# Technical Approach Report: Cynbit Intake Copilot

Anurag Chawla, 17 October 2026. Code: this repository. Reproduce results with `python scripts/train_eval.py`.

## 1. Scope

The proof of concept has four parts: (a) a sourced knowledge base with grounded Q&A, (b) a lead classifier, (c) case-study retrieval with a discovery-call brief, (d) a BitElevate track matcher. All run offline with no API key, so reviewers can run them anywhere.

**Not built:** an LLM generation layer. Section 6 describes the intended design. I did not implement or test it, so no result here depends on it.

## 2. Architecture

```
data/kb/*.json  ->  Retriever (TF-IDF, cosine)  ->  answer_question()  -> cited answer
inquiry text    ->  score_lead() rules  ->  signals  ->  LeadClassifier (TF-IDF + signals, logistic regression)
                ->  detect_services() + similar_case_studies()  ->  discovery_brief()
applicant text  ->  recommend_tracks() + recommend_duration()
app.py (Streamlit) exposes all three as tabs
```

## 3. Data pipeline

**Knowledge base.** 26 chunks collected by reading Cynbit's public pages (services, products, case studies, team, careers, blog, impact, BitElevate), registry listings, GitHub, and screenshots of the Instagram and LinkedIn pages. Each chunk records id, type, source URL, and a status of verified, claimed or inferred. Answers print the status next to each cited chunk so users can see how much to trust it. Thirteen case studies are stored separately with industry, service line, AI flag and tags.

**Lead training data.** Cynbit has no public inquiry log, so `src/lead_data.py` generates 1,500 messages from a latent-variable model. Each message has hidden attributes (real organisation, budget stated, timeline stated, contact provided, detail level) that choose phrase templates. The label comes from a weighted sum of those attributes plus Gaussian noise, so it correlates with, but is not identical to, the rule-based score. Spam, student, job-seeker and vendor messages (15% of data) are always Cold. Light typos and casing noise are added. The seed is fixed for reproducibility.

**Held-out test.** `data/leads/handwritten_test.json` holds 30 messages I wrote by hand, 10 per class, in natural phrasing different from the templates. Labels are my judgment, so they are subjective.

## 4. Models and why

| Component | Choice | Reason |
|---|---|---|
| Retrieval | TF-IDF (1-2 grams) with cosine similarity | Corpus is tiny (26 chunks); runs offline; results are explainable and testable |
| Lead classifier | Logistic regression on TF-IDF plus six engineered signals, class-balanced | Small data; interpretable; fast; strong baseline before heavier models |
| Signals | Specificity, budget, timeline, organisation, contact, service fit (from `score_lead`) | Encode what a sales person looks at; protect against memorising phrasing |
| Baseline | The rule-based score with thresholds 70 and 40 | Shows what ML adds over hand-written rules |

I did not use embeddings or a fine-tuned transformer: with 26 chunks and synthetic labels there is no evidence they would help, and they would add a download and an API or GPU dependency. They become sensible once real inquiry data exists.

## 5. Evaluation

Protocol: 5-fold stratified cross-validation on synthetic data, plus training on all synthetic data and testing on the 30 hand-written messages. Metric: macro-F1, because the three classes matter equally.

| Method | Synthetic CV macro-F1 | Hand-written macro-F1 | Hand-written accuracy |
|---|---|---|---|
| Rule-based score (baseline) | 0.557 +/- 0.035 | 0.535 | 0.567 |
| Logistic regression, text only | 0.720 +/- 0.018 | 0.438 | 0.500 |
| Logistic regression, text + signals | 0.757 +/- 0.004 | 0.706 | 0.733 |

Confusion matrix of the final model on the hand-written set (rows true, columns predicted; Cold, Warm, Hot):

```
[[10  0  0]
 [ 7  3  0]
 [ 0  1  9]]
```

**Findings.**
1. Text-only looks good in cross-validation (0.72) but falls to 0.44 on hand-written messages. It learned the generator's phrasing. Engineered signals recover most of the loss (0.71), so they carry the generalisation.
2. Hot is well identified (precision 1.00, recall 0.90). Cold recall is 1.00 but precision is 0.59 because Warm leads spill into Cold.
3. **Warm recall is 0.30.** Genuine-interest messages without a budget or timeline ("small boutique wants to sell online, what would it cost?") resemble junk like "need website, how much?" in the synthetic data. This is a label-definition problem as much as a model problem.

**Threats to validity.** Synthetic training data; a 30-message test set (one message moves accuracy by 3 points); labels written by the same person who built the system; signals reuse the same regex rules that define the baseline, so the baseline is not independent. Treat the numbers as evidence the pipeline works, not as expected production accuracy. The full output is in `reports/lead_model_eval.md`.

## 6. Planned LLM layer (design only, not implemented)

Purpose: turn the structured analysis into a readable discovery brief and a first-reply draft, always shown to a founder for approval.

- **Inputs:** inquiry text (contact details masked), predicted tier with probabilities, detected services, top three similar case studies, top knowledge-base chunks with their status tags.
- **Prompt rules:** use only the supplied context; cite chunk ids; never state "claimed" facts as verified; if information is missing, ask a question instead of inventing; no pricing promises; output fixed sections (summary, likely scope, past work, questions to ask, suggested reply).
- **Guardrails:** schema-checked output; reject any citation id not in the supplied context; low classifier confidence routes to a human with no draft; log edits as new training signal.
- **Evaluation before use:** a rubric on 30 real inquiries for faithfulness to context, usefulness, and tone, scored by a founder.

## 7. Execution plan

| Phase | Work | Output |
|---|---|---|
| 1. Data (week 1) | Export 3-6 months of inquiries with consent, mask contact details, label with founders | Real labelled set |
| 2. Model (week 2) | Retrain, add fresh holdout, fix Warm recall, calibrate probabilities, compare against embeddings | Report with confidence intervals |
| 3. Integrate (week 3) | Connect to the contact form and email inbox; show tier and brief in a shared sheet or CRM | Shadow mode, no auto-actions |
| 4. Pilot (weeks 4-5) | One founder uses it; measure response time, Hot precision, edited-brief rate | Go or no-go decision |
| 5. Harden | Monitoring for drift, retraining cadence, data retention policy | Runbook |

## 8. Testing and reproducibility

- `pytest` runs 8 tests: retrieval relevance, citations present, unknown questions return no sources, lead score ordering, service and case matching, brief content, generator determinism, and classifier separation of an obvious Hot from Cold.
- The model is not committed; `get_model()` trains it on first use, and `scripts/train_eval.py` retrains and rewrites the reports.
- Developed and tested on Python 3.13; dependencies in `requirements.txt`.

## 9. Limitations

Synthetic data; small test set; keyword-based service and track matching; no multilingual handling although Cynbit's customers likely write in Hindi and English; no live LLM; no authentication or storage in the app. These are listed so the next iteration targets them.
