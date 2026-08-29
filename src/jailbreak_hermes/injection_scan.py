"""Prompt-injection scanning for retrieved web text.

The invisible-character set and the override-pattern regex list are
lifted (with minor pruning) from NousResearch/hermes-agent:

  * tools/skills_guard.py  (INVISIBLE_CHARS)
  * tools/mcp_tool.py      (_MCP_INJECTION_PATTERNS)

We scan retrieved Exa results before feeding them to the generator so
adversarial text on the open web cannot redirect our pipeline.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


# --- ex-hermes: tools/skills_guard.py ----------------------------------
INVISIBLE_CHARS = {
    "​",  # zero-width space
    "‌",  # zero-width non-joiner
    "‍",  # zero-width joiner
    "⁠",  # word joiner
    "⁢",  # invisible times
    "⁣",  # invisible separator
    "⁤",  # invisible plus
    "﻿",  # zero-width no-break space (BOM)
    "‪",  # left-to-right embedding
    "‫",  # right-to-left embedding
    "‬",  # pop directional formatting
    "‭",  # left-to-right override
    "‮",  # right-to-left override
}

# --- ex-hermes: tools/mcp_tool.py --------------------------------------
INJECTION_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.I),
     "prompt override attempt ('ignore previous instructions')"),
    (re.compile(r"you\s+are\s+now\s+a", re.I),
     "identity override attempt ('you are now a...')"),
    (re.compile(r"your\s+new\s+(task|role|instructions?)\s+(is|are)", re.I),
     "task override attempt"),
    (re.compile(r"system\s*:\s*", re.I),
     "system prompt injection attempt"),
    (re.compile(r"<\s*(system|human|assistant)\s*>", re.I),
     "role tag injection attempt"),
    (re.compile(r"do\s+not\s+(tell|inform|mention|reveal)", re.I),
     "concealment instruction"),
    (re.compile(r"(curl|wget|fetch)\s+https?://", re.I),
     "network command in description"),
    (re.compile(r"base64\.(b64decode|decodebytes)", re.I),
     "base64 decode reference"),
    (re.compile(r"exec\s*\(|eval\s*\(", re.I),
     "code execution reference"),
]


@dataclass
class ScanResult:
    clean: bool
    findings: list[str]
    invisible_count: int

    def reason(self) -> str:
        if self.clean:
            return ""
        bits = list(self.findings)
        if self.invisible_count:
            bits.append(f"{self.invisible_count} invisible-unicode char(s)")
        return "; ".join(bits)


def scan(text: str) -> ScanResult:
    if not text:
        return ScanResult(clean=True, findings=[], invisible_count=0)
    invisible_count = sum(text.count(c) for c in INVISIBLE_CHARS)
    findings: list[str] = []
    for pattern, reason in INJECTION_PATTERNS:
        if pattern.search(text):
            findings.append(reason)
    return ScanResult(
        clean=not findings and invisible_count == 0,
        findings=findings,
        invisible_count=invisible_count,
    )


def strip_invisible(text: str) -> str:
    if not text:
        return text
    for c in INVISIBLE_CHARS:
        if c in text:
            text = text.replace(c, "")
    return text
