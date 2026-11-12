# HANDOFF

## 2026-11-12 저장소 연결
- USB 작업 폴더(연말정산) 자체를 GitHub `cho-kyeongseon/yearend`(main)에 연결했다.
- 로컬에만 있던 소스(app.py, bot.py, ingest.py, rag.py, make_deploy.py, 배포안내.md, .claude/launch.json)를 저장소에 추가했다.
- .gitignore로 원본 자료(PDF·ZIP·HWP, data/), .venv, `배포/` 폴더를 제외했다.
- Vercel 프로젝트는 이미 연결돼 있었다: https://yearend-teal.vercel.app

## 2026-11-12 배포 방식 정리
- `배포/` 폴더(옛 GitHub 업로드용 복사본)와 `make_deploy.py`를 삭제했다. 내용은 모두 GitHub 첫 커밋(a0c3349)에 남아 있다.
- 배포안내.md를 새 방식(USB 폴더에서 `build_web.py` 실행 → main 푸시 → Vercel 자동 배포)으로 고쳐 썼다.
