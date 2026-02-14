from __future__ import annotations

import json
from typing import Generator

import requests

from config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL, DEEPSEEK_MODEL



def llm_complete(messages: list[dict], temperature: float = 0.0, timeout: int = 60) -> str:
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "stream": False,
        "temperature": temperature,
    }
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]



def llm_stream(messages: list[dict], temperature: float = 0.75, timeout: int = 60) -> Generator[str, None, None]:
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "stream": True,
        "temperature": temperature,
    }
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    with requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, stream=True, timeout=timeout) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if not line:
                continue
            text = line.decode("utf-8")
            if not text.startswith("data:"):
                continue
            data = text.replace("data:", "", 1).strip()
            if data == "[DONE]":
                break
            chunk = json.loads(data)
            yield chunk["choices"][0]["delta"].get("content", "")
