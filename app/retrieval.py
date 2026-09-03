from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_-]*")


def tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


@dataclass
class Document:
    id: str
    title: str
    domain: str
    agency: str
    source_url: str
    text: str
    effective_date: str | None = None
    version: str = "1.0"


@dataclass
class Hit:
    document: Document
    score: float
    excerpt: str


class HybridRetriever:
    def __init__(self, documents: list[Document]):
        self.documents = documents
        self.df = Counter()
        for d in documents:
            self.df.update(set(tokens(d.title + " " + d.text)))

    @classmethod
    def from_json(cls, path: Path) -> "HybridRetriever":
        return cls([Document(**item) for item in json.loads(path.read_text())])

    def _lexical(self, query_terms: list[str], d: Document) -> float:
        counts = Counter(tokens(d.title + " " + d.text)); n = max(len(self.documents), 1)
        score = sum((1 + math.log(counts[t])) * math.log((n + 1) / (self.df[t] + 1)) for t in query_terms if counts[t])
        return score / max(math.sqrt(len(query_terms)), 1)

    def _semantic(self, query: str, d: Document) -> float:
        def vec(text: str) -> Counter:
            ts = tokens(text); out = Counter()
            for i in range(len(ts) - 1):
                out[hashlib.sha1(f"{ts[i]} {ts[i + 1]}".encode()).hexdigest()[:8]] += 1
            return out
        a, b = vec(query), vec(d.title + " " + d.text)
        dot = sum(a[k] * b[k] for k in a); den = math.sqrt(sum(v*v for v in a.values()) * sum(v*v for v in b.values()))
        return dot / den if den else 0.0

    def search(self, query: str, domain: str | None = None, top_k: int = 5) -> list[Hit]:
        qterms = tokens(query); scored: list[Hit] = []
        for d in self.documents:
            if domain and d.domain != domain: continue
            lexical = self._lexical(qterms, d); semantic = self._semantic(query, d)
            score = 0.35 * min(lexical / 5, 1.0) + 0.65 * semantic
            if any(t in d.title.lower() for t in qterms): score += 0.15
            if score > 0:
                start = next((d.text.lower().find(t) for t in qterms if d.text.lower().find(t) >= 0), 0)
                scored.append(Hit(d, round(score, 4), d.text[max(0, start-100):start+380].replace("\n", " ")))
        scored.sort(key=lambda h: (-h.score, h.document.id))
        return scored[:top_k]
