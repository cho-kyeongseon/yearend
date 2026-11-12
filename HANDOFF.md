# HANDOFF

## 2026-11-12 저장소 연결
- USB 작업 폴더(연말정산) 자체를 GitHub `cho-kyeongseon/yearend`(main)에 연결했다.
- 로컬에만 있던 소스(app.py, bot.py, ingest.py, rag.py, make_deploy.py, 배포안내.md, .claude/launch.json)를 저장소에 추가했다.
- .gitignore로 원본 자료(PDF·ZIP·HWP, data/), .venv, `배포/` 폴더를 제외했다.
- Vercel 프로젝트는 이미 연결돼 있었다: https://yearend-teal.vercel.app

## 다음에 할 일
- `배포/` 폴더와 `make_deploy.py`는 더 이상 필요 없음. 정리할지 결정.
