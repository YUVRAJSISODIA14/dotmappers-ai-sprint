"""
query_engine.py — Converts a natural-language question into SQL.

Stage 1 only: this generates SQL and prints it so we can sanity-check
the LLM's output before we let anything touch the real database.
"""

from app.llm import ask_llm

SCHEMA_DESCRIPTION = """
Table: tickets
Columns:
- ticket_id (TEXT): unique ticket identifier
- created_at (TEXT, format 'YYYY-MM-DD HH:MM:SS'): when the ticket was created
- category (TEXT): one of 'Technical', 'Billing', 'General'
- priority (TEXT): one of 'Low', 'Medium', 'High', 'Critical'
- status (TEXT): one of 'Open', 'Escalated', 'Resolved'
- response_time_hrs (REAL): hours until first response
- resolution_time_hrs (REAL, NULL if unresolved): hours until resolved
- agent_id (TEXT): which support agent handled the ticket
- customer_rating (REAL, NULL if unresolved): 1-5 customer rating
- issue_summary (TEXT): short free-text description
"""

SYSTEM_PROMPT = f"""You convert natural-language questions into a single SQLite SELECT query.

{SCHEMA_DESCRIPTION}

Rules:
- Output ONLY the raw SQL query. No explanation, no markdown fences, no semicolon at the end.
- Only ever generate SELECT statements. Never INSERT, UPDATE, DELETE, or DROP.
- Use exactly the column and table names given above.

Examples:
Question: How many critical tickets are unresolved?
SQL: SELECT COUNT(*) FROM tickets WHERE priority = 'Critical' AND status != 'Resolved'

Question: What is the average resolution time for billing tickets?
SQL: SELECT AVG(resolution_time_hrs) FROM tickets WHERE category = 'Billing'
"""


def generate_sql(question: str) -> str:
    """Asks the LLM to turn a natural-language question into a SQL query."""
    return ask_llm(prompt=question, system=SYSTEM_PROMPT).strip()

from app.data import get_connection


def execute_sql(sql: str):
    """
    Runs a SQL query against the tickets database, with a safety check.
    Only single SELECT statements are allowed — anything else is rejected
    before it ever touches the database.
    """
    cleaned = sql.strip().rstrip(";")

    if not cleaned.upper().startswith("SELECT"):
        raise ValueError(f"Refusing to run non-SELECT query: {cleaned}")
    if ";" in cleaned:
        raise ValueError(f"Refusing to run a multi-statement query: {cleaned}")

    conn = get_connection()
    try:
        cursor = conn.execute(cleaned)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
    finally:
        conn.close()

    return columns, rows                                     

def format_answer(question: str, columns, rows) -> str:
    """Turns a raw SQL result into a plain-English answer."""
    prompt = f"""Question: {question}
Query result — columns: {columns}, rows: {rows}

Answer the question in one plain sentence, using only the numbers given above. Do not mention SQL or databases."""
    return ask_llm(prompt=prompt).strip()


def answer_question(question: str) -> str:
    """Full pipeline: question -> SQL -> execute -> plain-English answer."""
    sql = generate_sql(question)
    columns, rows = execute_sql(sql)
    return format_answer(question, columns, rows)


if __name__ == "__main__":
    # Quick manual test — run: python -m app.query_engine
    test_questions = [
        "How many critical tickets are unresolved?",
        "Which agent has the lowest average customer rating?",
    ]
    for q in test_questions:
        print(f"Q: {q}")
        print(f"A: {answer_question(q)}")
        print()