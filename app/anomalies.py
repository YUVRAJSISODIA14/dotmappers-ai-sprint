"""
anomalies.py — Rule-based anomaly detection over the tickets table.

No LLM involved here — both checks are plain statistics and date
arithmetic, which is more reliable and auditable than asking a model
to "spot" anomalies in raw data.
"""
import json
import pandas as pd
from app.data import get_connection


def _load_dataframe() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM tickets", conn, parse_dates=["created_at"])
    conn.close()
    return df


def find_long_resolution_anomalies(df: pd.DataFrame = None) -> pd.DataFrame:
    """
    Flags resolved tickets whose resolution_time_hrs is a statistical
    outlier, using the standard IQR (interquartile range) method.
    """
    if df is None:
        df = _load_dataframe()

    resolved = df[df["resolution_time_hrs"].notna()]
    q1 = resolved["resolution_time_hrs"].quantile(0.25)
    q3 = resolved["resolution_time_hrs"].quantile(0.75)
    iqr = q3 - q1
    upper_fence = q3 + 1.5 * iqr

    flagged = resolved[resolved["resolution_time_hrs"] > upper_fence].copy()
    flagged["anomaly_reason"] = f"Resolution time exceeds {upper_fence:.1f}h (IQR upper fence)"
    return flagged


def find_stale_high_priority_anomalies(df: pd.DataFrame = None) -> pd.DataFrame:
    """
    Flags unresolved High/Critical tickets older than 24 hours, using
    the dataset's own latest created_at as the reference "now" — NOT
    the real system clock, since this dataset is static and historical.
    """
    if df is None:
        df = _load_dataframe()

    reference_now = df["created_at"].max()

    unresolved_high_priority = df[
        (df["status"].isin(["Open", "Escalated"]))
        & (df["priority"].isin(["High", "Critical"]))
    ].copy()

    age_hours = (reference_now - unresolved_high_priority["created_at"]).dt.total_seconds() / 3600
    flagged = unresolved_high_priority[age_hours > 24].copy()
    flagged["anomaly_reason"] = "Unresolved High/Critical ticket open more than 24h"
    return flagged


def get_all_anomalies() -> list:
    """Runs both checks and returns a combined list of anomaly records."""
    df = _load_dataframe()

    long_res = find_long_resolution_anomalies(df)
    stale = find_stale_high_priority_anomalies(df)


    combined = pd.concat([long_res, stale], ignore_index=True)
    # pandas/numpy values (NaN, int64, float64) aren't valid JSON on their own.
    # to_json() converts them correctly — NaN becomes null, numpy numbers
    # become plain numbers — then json.loads() turns that back into plain
    # Python dicts that FastAPI can safely return.
    return json.loads(combined.to_json(orient="records", date_format="iso"))


if __name__ == "__main__":
    # Quick manual test — run: python -m app.anomalies
    anomalies = get_all_anomalies()
    print(f"Found {len(anomalies)} anomalies total")
    for a in anomalies[:5]:
        print(a["ticket_id"], "-", a["anomaly_reason"])