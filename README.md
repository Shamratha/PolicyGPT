# PolicyGPT

PolicyGPT is a source-grounded prototype for finding and understanding Indian government schemes. It provides a citizen assistant for plain-language answers and eligibility guidance, plus an analyst workflow for comparing schemes and exporting an auditable report.

## Implemented

- Hybrid lexical and semantic retrieval over a versioned policy corpus.
- Domain routing across education, agriculture, MSME, finance, health, and disaster management.
- Profile-aware eligibility checks with explicit unknown fields.
- Claim-level citations and deterministic validation.
- Confidence and hallucination thresholds with one bounded repair pass.
- SQLite session/history storage and Markdown report export.
- Minimal browser UI, Docker packaging, and automated tests.

The bundled corpus is an illustrative seed dataset. Users must verify time-sensitive eligibility and apply through the official source.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000. API documentation is at `/docs`.

```bash
docker compose up --build
pytest -q
```

The staged agents are in `app/agents.py`; deterministic hybrid retrieval is in `app/retrieval.py`. See `docs/` for the Review 1 slide content, weekly progress entries, and rubric mapping.

## Review 1 deliverables

The generated presentation and filled weekly-progress workbook are in `deliverables/`:

- `PolicyGPT_Project_Work_2_Review_1.pptx`
- `PolicyGPT_Weekly_Progress_Report_Review_1.xlsx`

Regenerate them with `python scripts/generate_deliverables.py`. Student and guide signature cells intentionally remain placeholders for handwritten signing.
