# Lead classifier evaluation

Train: 1,500 synthetic inquiries (seed 7). Held-out: 30 hand-written inquiries (10 per class) written separately from the generator templates.

| Method | Synthetic 5-fold macro-F1 | Hand-written macro-F1 | Hand-written accuracy |
|---|---|---|---|
| Rule-based score (baseline) | 0.557 +/- 0.035 | 0.535 | 0.567 |
| Logistic regression, text only | 0.72 +/- 0.018 | 0.438 | 0.5 |
| Logistic regression, text + signals | 0.757 +/- 0.004 | 0.706 | 0.733 |

Confusion matrix on hand-written set, final model (rows = true, cols = predicted; order Cold, Warm, Hot):

```
[[10  0  0]
 [ 7  3  0]
 [ 0  1  9]]
```

```
              precision    recall  f1-score   support

        Cold       0.59      1.00      0.74        10
        Warm       0.75      0.30      0.43        10
         Hot       1.00      0.90      0.95        10

    accuracy                           0.73        30
   macro avg       0.78      0.73      0.71        30
weighted avg       0.78      0.73      0.71        30

```

Misclassified hand-written examples (8):

- true Hot, predicted Warm: Our restaurant chain (12 outlets) wants to auto-reply to Google reviews and spot complaint
- true Warm, predicted Cold: We have a small boutique and want to start selling online. Can you tell me what it would c
- true Warm, predicted Cold: Looking at automating some of our client onboarding with AI. Not sure where to start. Can 
- true Warm, predicted Cold: Interested in an app for our gym. We are thinking about it for next year. What do you usua
- true Warm, predicted Cold: Our company is exploring chatbots for support and comparing a few vendors. Do you have any
- true Warm, predicted Cold: Need SEO help for my clinic website, traffic dropped recently. What packages do you have?
- true Warm, predicted Cold: Looking for a development partner for a SaaS idea in HR tech. Still at the planning stage 
- true Warm, predicted Cold: We're a small manufacturing unit. Heard AI can help predict machine failures. Is this some