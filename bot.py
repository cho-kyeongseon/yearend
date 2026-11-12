"""연말정산 Q&A 봇 (검색 전용, 외부 AI 호출 없음).

질문 → 자료에서 BM25 검색 → 가장 관련 있는 대목(핵심 문장 강조)과 출처를 돌려준다.

CLI 테스트:  .venv\\Scripts\\python.exe bot.py "월세 세액공제 요건이 뭐야?"
"""
from __future__ import annotations

import re
import sys

from rag import INDEX_FILE, Retriever, tokenize

INDEX_READY = INDEX_FILE.exists()
TOP_K = 8          # 검색해 올 조각 수
MIN_SCORE = 8.0    # 이보다 낮으면 "관련 자료를 찾기 어렵다"고 안내

# 질문에 흔히 붙지만 검색에는 방해가 되는 말
_STOPWORDS = {
    "뭐야", "뭐예요", "뭔가요", "무엇", "무엇인가요", "알려줘", "알려주세요", "어떻게", "어떤",
    "되나요", "돼", "되는지", "있어", "있나요", "있는지", "해줘", "해주세요", "궁금", "궁금해",
    "하나요", "하는지", "인가요", "건가요", "얼마", "얼마나", "언제", "누가", "요즘", "그럼",
}
# 단어 끝 조사 (강조 표시용으로 떼어낸다)
_JOSA = re.compile(
    r"(으로|에서|에게|까지|부터|이랑|하고|이란|이면|려면|으면|은|는|이|가|을|를|에|의|도|로|와|과|만|요)$"
)
_WORD = re.compile(r"[가-힣]+|[A-Za-z]+|\d+")

_retriever: Retriever | None = None


def retriever() -> Retriever:
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever


def keywords(question: str) -> list[str]:
    """질문에서 검색·강조에 쓸 핵심 단어를 뽑는다."""
    out: list[str] = []
    for w in _WORD.findall(question):
        if w in _STOPWORDS:
            continue
        stem = _JOSA.sub("", w) if len(w) > 2 else w
        if len(stem) >= 2 and stem not in _STOPWORDS and stem not in out:
            out.append(stem)
    return out


def _best_window(text: str, kws: list[str], width: int = 5) -> str:
    """조각 안에서 핵심 단어가 가장 많이 몰린 몇 줄을 고른다."""
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    if len(lines) <= width:
        return "\n".join(lines)
    q = set(tokenize(" ".join(kws)))

    def score(ln: str) -> int:
        return len(q & set(tokenize(ln))) + sum(ln.count(k) for k in kws)

    scores = [score(ln) for ln in lines]
    # 핵심 단어가 몰린 구간을 찾고, 그 안에서 가장 관련 있는 줄이 가운데 오도록 맞춘다
    start = max(range(len(lines) - width + 1), key=lambda i: sum(scores[i : i + width]))
    peak = max(range(start, start + width), key=lambda i: scores[i])
    start = min(max(0, peak - width // 2), len(lines) - width)
    return "\n".join(lines[start : start + width])


def search(question: str) -> dict:
    """결과: {"keywords", "found", "results": [{source, loc, score, snippet, text}]}"""
    kws = keywords(question)
    query = " ".join(kws) or question
    hits = retriever().search(query, k=TOP_K * 2)

    results, seen = [], set()
    for h in hits:
        key = (h["source"], h["loc"])  # 같은 쪽에서 겹치는 조각은 하나만
        if key in seen:
            continue
        seen.add(key)
        results.append({**h, "snippet": _best_window(h["text"], kws)})
        if len(results) == TOP_K:
            break

    found = bool(results) and results[0]["score"] >= MIN_SCORE
    return {"keywords": kws, "found": found, "results": results}


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "월세액 세액공제를 받으려면 어떤 요건이 필요해?"
    r = search(q)
    print(f"핵심 단어: {r['keywords']}  /  관련 자료 {'있음' if r['found'] else '부족'}\n")
    for i, x in enumerate(r["results"], 1):
        print(f"[{i}] {x['source']} · {x['loc']} (점수 {x['score']})")
        print("    " + x["snippet"].replace("\n", "\n    ") + "\n")
