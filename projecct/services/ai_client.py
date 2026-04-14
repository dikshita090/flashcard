import json
import os
from pathlib import Path
from typing import Any

import requests


def load_env_file(base_dir: Path) -> dict[str, str]:
    env_path = base_dir / ".env" / ".env.example"
    values: dict[str, str] = {}
    if not env_path.exists():
        return values

    for line in env_path.read_text(encoding="utf-8").splitlines():
        clean_line = line.strip()
        if not clean_line or clean_line.startswith("#") or "=" not in clean_line:
            continue
        key, value = clean_line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def resolve_model_config(base_dir: Path, provider: str) -> dict[str, str]:
    env_values = load_env_file(base_dir)
    merged = {**env_values, **os.environ}
    provider = provider.lower()

    if provider == "auto":
        if merged.get("GROQ_API_KEY"):
            provider = "groq"
        elif merged.get("GEMINI_API_KEY"):
            provider = "gemini"

    if provider == "groq":
        return {
            "provider": "groq",
            "api_key": merged.get("GROQ_API_KEY", ""),
            "model": merged.get("GROQ_MODEL", "llama-3.3-70b-versatile"),
        }
    if provider == "gemini":
        return {
            "provider": "gemini",
            "api_key": merged.get("GEMINI_API_KEY", ""),
            "model": merged.get("GEMINI_MODEL", "gemini-1.5-flash"),
        }
    return {"provider": "offline", "api_key": "", "model": "offline"}


def generate_cards_with_llm(
    base_dir: Path,
    text: str,
    title: str,
    provider: str,
    requested_count: int = 18,
) -> list[dict[str, Any]]:
    config = resolve_model_config(base_dir, provider)
    if not config["api_key"] or config["provider"] == "offline":
        return []

    prompt = f"""
You are an expert teacher creating high-quality flashcards from study material.
Return only valid JSON with this structure:
{{
  "cards": [
    {{
      "question": "...",
      "answer": "...",
      "explanation": "...",
      "card_type": "concept|definition|relationship|example|edge_case",
      "difficulty_hint": "easy|medium|hard",
      "source_excerpt": "...",
      "tags": ["...","..."]
    }}
  ]
}}

Rules:
- Make {requested_count} cards if the source supports it.
- Cover concepts comprehensively, not superficially.
- Include a mix of definitions, reasoning, worked examples, relationships, and tricky cases.
- Keep each answer concise but complete.
- Avoid duplicate cards.
- The deck title is "{title}".
- Source text:
{text[:20000]}
""".strip()

    try:
        if config["provider"] == "groq":
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {config['api_key']}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": config["model"],
                    "temperature": 0.3,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": "You create rigorous educational flashcards."},
                        {"role": "user", "content": prompt},
                    ],
                },
                timeout=60,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
        else:
            response = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{config['model']}:generateContent?key={config['api_key']}",
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.3, "responseMimeType": "application/json"},
                },
                timeout=60,
            )
            response.raise_for_status()
            content = response.json()["candidates"][0]["content"]["parts"][0]["text"]

        payload = json.loads(content)
        cards = payload.get("cards", [])
        return [card for card in cards if card.get("question") and card.get("answer")]
    except Exception:
        return []
