"""Exa context retrieval.

The intent doc references Exa's hosted MCP endpoint
(`https://mcp.exa.ai/mcp`). That endpoint is JSON-RPC over HTTP and
requires the same EXA_API_KEY. To keep dependencies minimal, we hit
Exa's REST search endpoint (`https://api.exa.ai/search`) directly with
`httpx`. The retrieved sources are summarized, never transformed into
adversarial prompts, and are passed through the EvidenceGate before
the generator sees them.

Public surface deliberately mirrors what an MCP `tools/call` to Exa
would return so swapping in a real MCP client later is mechanical.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

import httpx

EXA_URL = "https://api.exa.ai/search"


class ExaError(RuntimeError):
    pass


@dataclass
class ExaSource:
    id: str
    title: str
    url: str
    snippet: str
    published: str | None = None
    score: float | None = None


@dataclass
class RetrievalResult:
    query: str
    sources: list[ExaSource] = field(default_factory=list)
    raw: dict | None = None


def _api_key() -> str:
    key = os.environ.get("EXA_API_KEY")
    if not key:
        raise ExaError("EXA_API_KEY environment variable not set")
    return key


def search(
    query: str,
    *,
    num_results: int = 5,
    include_text: bool = True,
    timeout: float = 30.0,
) -> RetrievalResult:
    """One Exa search call. India-context relevance is the *caller's*
    responsibility — see evidence_gate.filter_sources."""
    headers = {
        "x-api-key": _api_key(),
        "Content-Type": "application/json",
    }
    payload: dict = {
        "query": query,
        "numResults": num_results,
        "type": "auto",
    }
    if include_text:
        payload["contents"] = {"text": {"maxCharacters": 2000}}

    with httpx.Client(timeout=timeout) as client:
        resp = client.post(EXA_URL, headers=headers, json=payload)
    if resp.status_code >= 400:
        raise ExaError(f"Exa {resp.status_code}: {resp.text[:500]}")
    data = resp.json()

    sources: list[ExaSource] = []
    for i, item in enumerate(data.get("results", [])):
        sources.append(
            ExaSource(
                id=f"src_{i:03d}",
                title=item.get("title") or "",
                url=item.get("url") or "",
                snippet=(item.get("text") or item.get("snippet") or "")[:2000],
                published=item.get("publishedDate"),
                score=item.get("score"),
            )
        )
    return RetrievalResult(query=query, sources=sources, raw=data)
