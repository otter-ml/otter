# 🦦 Otter — Talk to your data, get ML models

**The ML framework that speaks human.**

Otter is a conversational AI tool that helps you turn spreadsheets and databases into machine learning predictions — no coding, no ML knowledge needed.

Open a terminal. Type `otter`. Chat.

```
$ otter

🦦 Hey! I'm Otter. I help you turn data into predictions.
   What are you working with today?

> I have a CSV with customer data, want to predict who will leave

🦦 Let's take a look. What's the file path?

> ~/data/customers.csv

📂 Loaded customers.csv — 45,000 rows × 12 columns

🦦 I see a "churned" column with yes/no values — that's probably
   what you want to predict. I also see signup_date, monthly_spend,
   support_tickets, and 8 other columns.

   Want me to build a model that predicts which customers will churn?

> yes please

🏋️ Training...

🦦 Done! The model correctly predicts churn 89% of the time.
   The biggest factors: monthly_spend (customers who spend less
   tend to leave) and support_tickets (more tickets = higher risk).

   Want me to save this model so you can use it later?
```

## Install

```bash
pip install otter-ml
```

## Quick Start

```bash
# Launch the chat interface
otter

# Show your configuration
otter config

# Version
otter --version
```

On first launch, Otter will ask you to pick an AI provider and enter your API key. Takes 30 seconds.

## AI Providers

| Provider | Model | API Key? | Cost |
|----------|-------|----------|------|
| **Anthropic** | Claude 3.5 Haiku | Yes | Pay per use |
| **OpenAI** | GPT-4o Mini | Yes | Pay per use |
| **Ollama** | Llama 3.2 | No (local) | Free |
| **OpenRouter** | Multiple models | Yes | Pay per use |

**Recommendation:** Ollama for free local use, Anthropic for best quality.

## What Can Otter Do?

- **Load data** from CSV, Excel, JSON, Parquet, or any SQL database
- **Understand your data** — column types, missing values, patterns
- **Build ML models** — classification and regression, auto-tuned
- **Explain results** — in plain language, not jargon
- **Export models** — save and reuse your trained models

## Requirements

- Python 3.10+
- A terminal that supports colors (most do)
- An AI provider API key (or Ollama installed locally)

## License

MIT
