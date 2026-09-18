# Support Ticket AI System

An AI-powered system for querying and monitoring a support ticket dataset in natural language, built for the DOTMappers AI Engineer assessment.

## What it does

- Ingests a 500-row support ticket dataset into SQLite
- Answers natural-language questions about the data (e.g. "How many critical tickets are unresolved?")
- Detects two categories of anomalies: statistically long resolution times, and unresolved high-priority tickets sitting open too long
- Exposes both a REST API and a web UI covering the same functionality

## Setup

1. Clone the repo and enter the folder:

git clone https://github.com/YUVRAJSISODIA14/dotmappers-ai-sprint.git
cd dotmappers-ai-sprint

2. Create and activate a virtual environment:

python -m venv venv
venv\Scripts\activate # Windows
source venv/bin/activate # Mac/Linux

3. Install dependencies:

pip install -r requirements.txt

4. Add your Groq API key. Create a `.env` file in the project root:

GROQ_API_KEY=your_key_here

   Get a free key at [console.groq.com](https://console.groq.com) — no card required.
5. Start everything with one command:

run.bat

   This launches the FastAPI server (`http://127.0.0.1:8000`) in its own window and opens the Streamlit UI (`http://localhost:8501`) in your browser.

## Architecture

**Data layer** — `support_tickets.csv` is loaded once into a local SQLite database (`data/tickets.db`) on first run. SQLite over pure in-memory pandas was chosen because FastAPI serves concurrent requests, and a real `.db` file is simpler to share safely across requests than keeping one connection alive for the app's whole lifetime.

**Natural-language querying (text-to-SQL)** — rather than sending the LLM the raw dataset and asking it to reason over every row, the system uses a three-stage pipeline:
1. **Generate**: the LLM is given the exact table schema plus a couple of worked examples, and converts the user's question into a single SQL `SELECT` statement.
2. **Execute**: the query runs directly against SQLite. All arithmetic and filtering is done by the database, not the model — this guarantees correctness and makes results auditable.
3. **Format**: the raw result is turned into a one-sentence natural-language answer.

This was chosen over asking the LLM to answer directly from raw context because it separates "understanding the question" (something LLMs are good at) from "computing the answer" (something a database is exact at, and an LLM is not).

A safety check rejects any generated query that isn't a plain `SELECT` statement before it ever reaches the database, in case the model doesn't follow instructions.

**Anomaly detection** — implemented as two rule-based checks rather than an LLM call, since these are well-defined statistical/logical conditions where deterministic code is both faster and more auditable:
- **Long resolution times**: an IQR (interquartile range) outlier check on `resolution_time_hrs` among resolved tickets. The upper fence sits at ~48.1 hours, flagging 21 of 500 tickets.
- **Stale high-priority tickets**: unresolved (Open/Escalated) tickets with High or Critical priority, open more than 24 hours. **Design note:** "now" is defined as the latest `created_at` timestamp in the dataset, not the real system clock — since this dataset is static and dated 2024, using the real clock would trivially flag all 80 matching tickets as "old" regardless of their actual relative age. Using the dataset's own timeline makes the check meaningful rather than vacuous.

Combined, these two checks currently flag 101 anomalies.

**API + UI** — the assessment brief was ambiguous about whether the REST API and UI were both required or alternatives (Section 2 states both are required; the deliverables list frames them as an either/or). Both were built to satisfy either reading. Both share the same underlying Python functions (`query_engine.py`, `anomalies.py`) rather than the UI calling the API over HTTP — this avoids duplicating logic and means either surface can be used independently.

## Tech stack / models

- **Language**: Python
- **API**: FastAPI + Uvicorn
- **UI**: Streamlit
- **Data**: pandas, SQLite
- **LLM**: Groq API (free tier), model `openai/gpt-oss-20b` — chosen for fast inference and no cost, sufficient for this dataset's schema complexity. The LLM call is isolated in `llm.py` so switching models or providers (e.g. to a local Ollama model) only requires changing that one file.

## API Endpoints

| Method | Endpoint     | Description                                  |
|--------|-------------|-----------------------------------------------|
| GET    | `/health`    | Health check                                  |
| POST   | `/query`     | Body: `{"question": "..."}` — returns a plain-English answer |
| GET    | `/anomalies` | Returns all currently detected anomalies      |

## Example queries and outputs

**Q: How many critical tickets are unresolved?**
> A: There are 31 critical tickets unresolved.

SQL generated: `SELECT COUNT(*) FROM tickets WHERE priority = 'Critical' AND status != 'Resolved'`

**Q: Which agent has the lowest average customer rating?**
> A: AGT-08 has the lowest average customer rating.

SQL generated: `SELECT agent_id, AVG(customer_rating) AS avg_rating FROM tickets WHERE customer_rating IS NOT NULL GROUP BY agent_id ORDER BY avg_rating ASC LIMIT 1`

## Limitations
- Time-relative questions ("this month," "this week," "today") are interpreted against the real system clock, not the dataset's own timeline — since this dataset is historical (Jan–Mar 2024), such questions will correctly return zero results rather than mapping to the data's actual time range. A production version would need an explicit reference-date concept.
- The natural-language query engine and the anomaly-detection engine are separate systems. Questions like "are there any anomalies..." go through text-to-SQL (which has no concept of "anomaly") rather than the dedicated anomaly logic — asking about anomalies should use the `/anomalies` endpoint or the UI's anomaly panel directly, not the query box.
- Only `SELECT` statements are permitted by design — the system cannot modify data, by intention, not as an oversight.
- Anomaly thresholds (IQR multiplier, 24-hour window) are fixed constants, not user-configurable, for scope reasons.
- No authentication on the API endpoints — acceptable for this local/demo scope, but would need adding before any real deployment.
- No automated test suite was built given the assessment's time constraints; correctness was validated manually against the dataset's known statistics instead.
- The "current time" used for the stale-ticket check is anchored to the dataset's own latest timestamp rather than the real clock — appropriate for this static historical dataset, but a live production system would need a different strategy (e.g. an explicit reference-date parameter).