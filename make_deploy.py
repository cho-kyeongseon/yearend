"""Vercel 배포용 '배포' 폴더를 만든다. 이 폴더 안의 내용을 GitHub 저장소에 올리면 된다.

사용법:  .venv\\Scripts\\python.exe make_deploy.py
FAQ·체크리스트를 고치거나 자료를 새로 색인(ingest.py)한 뒤 다시 실행한다.
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "배포"
FILES = [
    "vercel.json", "build_web.py", "checklist.py", "faq.py", "index/chunks.json",
    "web/index.html", "web/style.css", "web/app.js", "web/data/content.json", "web/data/chunks.json",
]
README = """# 연말정산 도우미

국세청 2025년 귀속 연말정산 안내 자료를 근거로 공제 여부를 안내하는 웹페이지입니다.

- 💬 상담하기: 카카오톡처럼 질문하면 요건·자주 묻는 질문 답변을 보여줍니다.
- ✅ 공제 체크리스트: 네/아니오로 답하며 공제 가능 여부를 확인합니다.
- 🔎 자료 검색: 안내 자료 원문을 찾아봅니다.

## 내용 고치기
- 자주 묻는 질문: `faq.py`
- 체크리스트 질문·요건 요약·알아듣는 단어: `checklist.py`

GitHub에서 파일을 고치고 저장(Commit)하면 Vercel이 `build_web.py`를 실행해 `web/data/content.json`을 다시 만들고 자동으로 배포합니다.

일반적인 안내이며 세무 자문이 아닙니다. 최종 판단은 회사 담당자나 국세상담센터(☎126)에 확인하세요.
"""


def main() -> None:
    sys.path.insert(0, str(ROOT))
    import build_web
    build_web.main()  # 질문 흐름·FAQ 검증 + 웹 데이터 최신화

    # 이전 내용을 비우되 .git(GitHub 업로드 기록)은 남긴다
    OUT.mkdir(exist_ok=True)
    for p in OUT.iterdir():
        if p.name == ".git":
            continue
        shutil.rmtree(p) if p.is_dir() else p.unlink()
    for f in FILES:
        dst = OUT / f
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / f, dst)
    (OUT / "README.md").write_text(README, encoding="utf-8")

    total = sum(p.stat().st_size for p in OUT.rglob("*") if p.is_file())
    print(f"\n배포 폴더 준비 완료: {OUT}  ({total / 1024 / 1024:.1f} MB)")
    for p in sorted(OUT.rglob("*")):
        if p.is_file():
            print("  -", p.relative_to(OUT).as_posix())


if __name__ == "__main__":
    main()
