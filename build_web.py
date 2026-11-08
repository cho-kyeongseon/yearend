"""checklist.py · faq.py · index/chunks.json 을 웹페이지(web/)가 읽는 데이터로 바꾼다.

사용법:  python build_web.py
Vercel에서는 배포할 때마다 이 스크립트가 자동으로 실행된다 (vercel.json 참고).
Python 기본 기능만 사용하므로 별도 설치가 필요 없다.
"""
import json
import shutil
from pathlib import Path

import checklist
import faq

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "web" / "data"


def main() -> None:
    checklist.validate()
    faq.validate()
    DATA.mkdir(parents=True, exist_ok=True)

    content = {
        "DOCS": checklist.DOCS,
        "DOC_TITLES": checklist.DOC_TITLES,
        "GROUPS": checklist.GROUPS,
        "ITEMS": checklist.ITEMS,
        "SUMMARY": checklist.SUMMARY,
        "KEYWORDS": {k: {"words": words, "weight": w} for k, (words, w) in checklist.KEYWORDS.items()},
        "FAQS": faq.FAQS,
        "POPULAR": faq.POPULAR,
        "CASE_LABELS": faq.CASE_LABELS,
    }
    (DATA / "content.json").write_text(json.dumps(content, ensure_ascii=False), encoding="utf-8")
    shutil.copy2(ROOT / "index" / "chunks.json", DATA / "chunks.json")
    print(f"웹 데이터 생성 완료: 항목 {len(checklist.ITEMS)}개, FAQ {len(faq.FAQS)}개 -> {DATA}")


if __name__ == "__main__":
    main()
