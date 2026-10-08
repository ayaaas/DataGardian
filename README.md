# DataGuardian 🌸

Upload a CSV → Python quality engine → chat with the AI Data Quality Investigator.

```
dataguardian/
├── backend/      FastAPI app + quality engine + prompt
├── frontend/     index.html (served by the backend)
├── data/         sample_dataset.csv, quality_report.json
├── notebooks/    DataGuardian_Prototype.ipynb
└── .env          (create from .env.example; "_env" also works)
```

## Run
```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
cp .env.example .env                                   # then add your GROQ_API_KEY
uvicorn backend.app:app --reload
```
Open http://127.0.0.1:8000 — upload a CSV or click "Try the sample dataset".

## Notes
- Only the computed quality report (stats, column names, category variants) is sent to the LLM, never raw rows.
- Sessions live in server memory and reset when the server restarts.
- API docs: http://127.0.0.1:8000/docs
