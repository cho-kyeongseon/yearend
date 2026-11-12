"""한국어 BM25 검색 (글자 2-gram 기반, 외부 형태소 분석기 불필요)."""
from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

INDEX_FILE = Path(__file__).resolve().parent / "index" / "chunks.json"
_WORD = re.compile(r"[가-힣]+|[a-z]+|\d+")


def tokenize(text: str) -> list[str]:
    toks: list[str] = []
    for w in _WORD.findall(text.lower()):
        if "가" <= w[0] <= "힣" and len(w) > 1:
            toks.extend(w[i : i + 2] for i in range(len(w) - 1))
        else:
            toks.append(w)
    return toks


class Retriever:
    def __init__(self, path: Path = INDEX_FILE, k1: float = 1.5, b: float = 0.75):
        self.chunks: list[dict] = json.loads(path.read_text(encoding="utf-8"))
        self.k1, self.b = k1, b
        self.postings: dict[str, list[tuple[int, int]]] = defaultdict(list)
        self.lengths: list[int] = []
        for i, c in enumerate(self.chunks):
            tf = Counter(tokenize(c["source"] + " " + c["text"]))
            self.lengths.append(sum(tf.values()))
            for t, n in tf.items():
                self.postings[t].append((i, n))
        self.avgdl = sum(self.lengths) / max(len(self.lengths), 1)
        n_docs = len(self.chunks)
        self.idf = {
            t: math.log(1 + (n_docs - len(p) + 0.5) / (len(p) + 0.5))
            for t, p in self.postings.items()
        }

    def search(self, query: str, k: int = 8) -> list[dict]:
        scores: dict[int, float] = defaultdict(float)
        for t, qn in Counter(tokenize(query)).items():
            idf = self.idf.get(t)
            if idf is None:
                continue
            for doc, tf in self.postings[t]:
                norm = tf + self.k1 * (1 - self.b + self.b * self.lengths[doc] / self.avgdl)
                scores[doc] += qn * idf * tf * (self.k1 + 1) / norm
        top = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]
        return [{**self.chunks[d], "score": round(s, 2)} for d, s in top]
