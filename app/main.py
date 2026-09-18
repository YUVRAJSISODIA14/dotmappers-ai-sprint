"""
main.py — FastAPI layer exposing the query engine and anomaly detection.
"""

from fastapi import FastAPI

app = FastAPI(title="Support Ticket AI System")


@app.get("/health")
def health():
    """Simple check that the server is up."""
    return {"status": "ok"}
from pydantic import BaseModel
from app.query_engine import answer_question


class QueryRequest(BaseModel):
    question: str


@app.post("/query")
def query(request: QueryRequest):
    """Takes a natural-language question, returns a plain-English answer."""
    answer = answer_question(request.question)
    return {"question": request.question, "answer": answer}
from app.anomalies import get_all_anomalies


@app.get("/anomalies")
def anomalies():
    """Returns all currently detected anomalies."""
    return {"anomalies": get_all_anomalies()}