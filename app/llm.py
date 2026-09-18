"""
llm.py — Thin wrapper around the Groq API.

Keeping every LLM call behind this one function means if you ever want to
swap providers (e.g. to a local Ollama model for a fully offline setup),
this is the only file that changes.
"""

import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()  # reads GROQ_API_KEY from .env into the environment

_client = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY not found. Make sure it's set in your .env file."
            )
        _client = Groq(api_key=api_key)
    return _client


def ask_llm(prompt: str, system: str = "", model: str = "openai/gpt-oss-20b") -> str:
    """
    Sends a prompt to Groq and returns the plain text response.

    system: optional system-level instruction (role, constraints, tone).
    model: which Groq-hosted model to use.
    """
    client = _get_client()

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0,  # deterministic-ish output — matters for generating SQL
    )

    return response.choices[0].message.content.strip()


if __name__ == "__main__":
    # Quick manual test — run: python -m app.llm
    print(ask_llm("Say hello in exactly three words."))