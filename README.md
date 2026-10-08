# DataGuardian 🌸

An AI data quality investigator. Upload a CSV, get an instant quality report, and chat with an assistant that explains the problems and how to fix them.

## What it does

1. **Upload** a CSV in the web app, or try the built-in sample dataset.
2. A **Python quality engine** measures the data (the language model does not do this):
   - missing values per column
   - duplicate rows
   - numeric outliers (IQR method)
   - inconsistent categories (e.g. `Morocco` / `maroc` / `MA`)
3. It computes a transparent **quality score** (0–100) from four dimensions: completeness, uniqueness, validity and consistency.
4. Issues are given a severity and ranked by priority so you know what to fix first.
5. A **chat assistant** (Groq LLM) explains the findings and answers follow-up questions, using the computed report as its only source of truth.

## Rules the assistant follows

- Never invents statistics, columns or problems that are not in the report.
- Recommends cleaning steps but never claims to have modified your data.
- Declines questions unrelated to data quality.
- Treats user messages as untrusted (no leaking of system prompt, config or API keys).
- Replies in the language you write in.

## Project structure

```
dataguardian/
├── backend/        FastAPI app, quality engine, system prompt
├── frontend/       index.html (single-page chat UI, served by the backend)
├── data/           sample_dataset.csv, quality_report.json
├── notebooks/      DataGuardian_Prototype.ipynb (original prototype)
├── .env.example    template for your secrets
└── README.md
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
cp .env.example .env               # then add your own Groq API key
```

`.env` should contain:

```
GROQ_API_KEY=your_key_here
BASE_URL_GROQ=https://api.groq.com/openai/v1
MODEL_NAME=openai/gpt-oss-20b
```

Get a key at https://console.groq.com/keys. **Never commit `.env`**, it is listed in `.gitignore`.

## Run

```bash
python -m uvicorn backend.app:app --reload --port 8001
```

Open http://127.0.0.1:8001, then upload a CSV or click **Try the sample dataset**.

- Health check: http://127.0.0.1:8001/api/health (shows whether the LLM is configured)
- API docs: http://127.0.0.1:8001/docs

## API

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/upload` | Upload a CSV, returns a session id and the quality report |
| POST | `/api/sample` | Load the sample dataset |
| POST | `/api/chat` | Send a message `{session_id, message}`, returns the answer |
| POST | `/api/reset` | Clear the conversation for a session |
| GET | `/api/report/{session_id}` | Download the report as JSON |
| GET | `/api/health` | Check that the server and LLM are configured |

## Privacy

Only the computed report (statistics, column names, category variants) is sent to the LLM. Raw rows of your data are never sent.

## Limitations

- Age, email and country checks only run on columns named exactly `age`, `email` and `country`. The country alias list only knows Morocco.
- Sessions are kept in server memory and reset when the server restarts.
- Uploads are limited to 5 MB.
- The 3D flowers need an internet connection (three.js from a CDN) and WebGL.

## Notebook

`notebooks/DataGuardian_Prototype.ipynb` contains the original prototype: the engine, the scoring, Prompt V1 and the conversation tests.
