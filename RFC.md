# RFC-001: Otter — AI-Powered ML Framework

**Status:** Draft  
**Date:** 2026-02-19  
**Authors:** Omar Hernandez, TARS

---

## 1. Problem

Most organizations have years of accumulated data in databases, spreadsheets, or files — and have no idea they can use it to make predictions. The barrier isn't the data. It's the expertise gap:

- Hiring an ML engineer costs $100-150k/year
- Cloud AutoML tools (SageMaker, Vertex AI) require ML knowledge to configure
- Jupyter notebooks are fine for researchers, not for engineers who just want results
- No tool today says: "connect your database, tell me what you want to predict, I'll do the rest"

**Otter solves this.** It's a CLI-first, AI-powered ML framework for engineers who know their data but not ML.

---

## 2. Vision

```
otter connect --db postgresql://mydb
otter analyze
otter train --goal "predict customer churn"
otter eval
otter sandbox
otter export --format onnx
```

Six commands. Zero ML knowledge required.

---

## 3. Target User

**Primary:** Software engineers / backend devs at startups (10-200 people) who:
- Have a production database with historical data
- Want ML-powered predictions without hiring a data scientist
- Are comfortable with CLI tools
- Don't want to learn PyTorch or scikit-learn internals

**Secondary:** ML engineers who want to skip boilerplate and go straight to results.

---

## 4. Core Commands

### `otter connect`
Connect to a data source.

```bash
otter connect --db postgresql://user:pass@host/db
otter connect --file ./customers.csv
otter connect --file ./data.json
```

- Inspects schema / columns
- Infers data types, cardinality, nulls
- Stores connection config locally (`~/.otter/config.json`)

---

### `otter analyze`
AI analyzes your data and suggests what you can predict.

```bash
otter analyze
```

Output:
```
🦦 Otter analyzed your data (customers table, 45,231 rows, 18 columns)

I found 3 prediction opportunities:

  1. 📉 Customer churn — predict who will cancel in the next 30 days
     Confidence: High | Relevant columns: last_login, plan_type, support_tickets
  
  2. 💰 Revenue forecast — predict monthly revenue per customer
     Confidence: Medium | Relevant columns: transactions, plan_type, signup_date
  
  3. 🚨 Fraud detection — flag suspicious transactions
     Confidence: Medium | Relevant columns: amount, location, device_id, time

Run: otter train --goal "customer churn"
```

---

### `otter train`
Train a model for a specific goal.

```bash
otter train --goal "predict customer churn"
otter train --goal "predict customer churn" --target churn_label --auto-tune
```

Steps (with progress output):
1. Feature engineering (AI selects + transforms relevant columns)
2. Model selection (tries 3-5 candidates: XGBoost, LightGBM, RandomForest, LogReg)
3. Hyperparameter tuning (Optuna, 50 trials by default)
4. Cross-validation (5-fold)
5. Saves best model to `~/.otter/models/<name>/`

Output:
```
🦦 Training customer_churn model...

  ✓ Feature engineering    (12 features selected)
  ✓ Model selection        (XGBoost wins: AUC 0.91 vs LightGBM 0.89)
  ✓ Hyperparameter tuning  (50 trials, best params found)
  ✓ Cross-validation       (5-fold AUC: 0.91 ± 0.02)

Model saved: ~/.otter/models/customer_churn/
Run: otter eval
```

---

### `otter eval`
Evaluate the trained model with human-readable metrics.

```bash
otter eval
otter eval --model customer_churn
```

Output:
```
🦦 Model: customer_churn (XGBoost)

  Accuracy:   87.3%
  AUC-ROC:    0.91
  Precision:  84.1%  (of predicted churners, 84% actually churned)
  Recall:     79.6%  (caught 79% of actual churners)
  F1 Score:   0.82

📊 What this means:
  For every 100 customers predicted to churn, ~84 will actually churn.
  You'll miss ~20% of real churners. Good for a first model.

🔍 Top features driving predictions:
  1. days_since_login     (importance: 0.31)
  2. support_tickets_30d  (importance: 0.24)
  3. plan_type            (importance: 0.18)

💡 Suggestion: Collect more data on support ticket sentiment to improve recall.
```

---

### `otter sandbox`
Interactive testing of the trained model.

```bash
otter sandbox
otter sandbox --model customer_churn
```

Launches an interactive prompt:
```
🦦 Sandbox mode — customer_churn model
Type values to test predictions. Ctrl+C to exit.

> last_login: 45 days ago
> support_tickets: 3
> plan_type: basic

Prediction: CHURN (87% probability)
Explanation: High days since login + multiple support tickets strongly indicate churn risk.

Try another? (y/n)
```

---

### `otter export`
Export trained model for production use.

```bash
otter export --format onnx
otter export --format pickle
otter export --format api        # generates FastAPI wrapper
```

Output:
```
🦦 Exported customer_churn model

  Format: ONNX
  File:   ./otter_export/customer_churn.onnx
  Size:   2.3 MB

  Usage example:
    import onnxruntime as rt
    sess = rt.InferenceSession("customer_churn.onnx")
    result = sess.run(None, {"input": your_features})
```

---

## 5. Architecture

```
otter/
├── otter/                  # Python package
│   ├── __init__.py
│   ├── cli.py              # Typer CLI entry point
│   ├── connect/            # Data source connectors
│   │   ├── db.py           # SQLAlchemy-based DB connector
│   │   ├── file.py         # CSV, JSON, Parquet loader
│   │   └── schema.py       # Schema inference
│   ├── analyze/            # AI-powered data analysis
│   │   ├── profiler.py     # Column stats, cardinality, nulls
│   │   └── suggester.py    # LLM-powered use case suggestions
│   ├── train/              # Training pipeline
│   │   ├── features.py     # Feature engineering
│   │   ├── selector.py     # Model selection (XGB, LGBM, RF, LR)
│   │   ├── tuner.py        # Optuna hyperparameter tuning
│   │   └── pipeline.py     # Orchestrator
│   ├── eval/               # Evaluation + explainability
│   │   ├── metrics.py      # Standard ML metrics
│   │   └── explainer.py    # SHAP + human-readable output
│   ├── sandbox/            # Interactive testing
│   │   └── repl.py         # Interactive prediction shell
│   ├── export/             # Model export
│   │   ├── onnx.py
│   │   ├── pickle.py
│   │   └── api.py          # FastAPI code generator
│   └── ai/                 # LLM integration
│       ├── client.py       # Anthropic / OpenAI client
│       └── prompts.py      # All system prompts
├── tests/
├── docs/
├── pyproject.toml
├── README.md
└── RFC.md
```

---

## 6. Tech Stack

| Layer | Choice | Why |
|-------|--------|-----|
| CLI | Typer | Modern, type-safe, great UX |
| ML | scikit-learn + XGBoost + LightGBM | Battle-tested, local, fast |
| Hyperparameter tuning | Optuna | Best-in-class, lightweight |
| Data | pandas + SQLAlchemy | Standard, broad connector support |
| Explainability | SHAP | Industry standard |
| AI layer | Anthropic Claude API (claude-3-5-haiku) | Fast, cheap for analysis tasks |
| Export | ONNX + pickle | Broadest compatibility |
| Config | platformdirs + JSON | Cross-platform, simple |

**AI is optional** — `otter analyze` and natural language explanations need an API key. Core training works 100% locally without it.

---

## 7. Installation

```bash
pip install otter-ml
```

Or with uv:
```bash
uv add otter-ml
```

Optional AI features:
```bash
pip install otter-ml[ai]
export ANTHROPIC_API_KEY=sk-...
```

---

## 8. MVP Scope (v0.1)

**In:**
- `otter connect` — CSV + PostgreSQL
- `otter analyze` — schema profiling + AI suggestions (optional)
- `otter train` — classification only (churn, fraud, binary predictions)
- `otter eval` — standard metrics + SHAP top features
- `otter sandbox` — interactive CLI
- `otter export --format pickle`

**Out (v0.2+):**
- Regression tasks
- Time series
- ONNX export
- FastAPI wrapper generation
- MySQL / MongoDB connectors
- Web UI

---

## 9. Go-to-Market (Open Source Strategy)

**Phase 1 — Build in public (weeks 1-4)**
- Ship v0.1 with a compelling demo
- Demo: connect a public Kaggle dataset (Titanic or Churn) → full pipeline in 2 min
- Post on Reddit (r/MachineLearning, r/Python, r/datascience)
- Hacker News Show HN post

**Phase 2 — Community (weeks 5-12)**
- GitHub Discussions for feedback
- Add connectors users request
- Build showcase of real use cases

**Phase 3 — Monetization (v1.0+)**
- **Otter Cloud** — sync experiments, team collaboration, hosted models ($29-99/mo)
- **Enterprise** — on-premise, SSO, audit logs

---

## 10. Success Metrics

| Metric | Target (3 months) |
|--------|-------------------|
| GitHub stars | 500+ |
| PyPI downloads | 1,000+/month |
| HN front page | Once |
| Contributors | 5+ |

---

## 11. What We're NOT Building

- Another Jupyter notebook interface
- A cloud-only product
- A drag-and-drop AutoML UI
- A deep learning framework (PyTorch/TF territory)

Otter is the tool between "I have data" and "I have a working model". That's it.

---

*Next step: implement v0.1 skeleton*
