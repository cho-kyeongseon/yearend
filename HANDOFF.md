# HANDOFF

## 2026-11-12 저장소 연결
- USB 작업 폴더(연말정산) 자체를 GitHub `cho-kyeongseon/yearend`(main)에 연결했다.
- 로컬에만 있던 소스(app.py, bot.py, ingest.py, rag.py, make_deploy.py, 배포안내.md, .claude/launch.json)를 저장소에 추가했다.
- .gitignore로 원본 자료(PDF·ZIP·HWP, data/), .venv, `배포/` 폴더를 제외했다.
- Vercel 프로젝트는 이미 연결돼 있었다: https://yearend-teal.vercel.app

## 2026-11-12 배포 방식 정리
- `배포/` 폴더(옛 GitHub 업로드용 복사본)와 `make_deploy.py`를 삭제했다. 내용은 모두 GitHub 첫 커밋(a0c3349)에 남아 있다.
- 배포안내.md를 새 방식(USB 폴더에서 `build_web.py` 실행 → main 푸시 → Vercel 자동 배포)으로 고쳐 썼다.

## 2026-11-12 USB 휴대용 파이썬으로 전환
- 기존 .venv는 다른 PC(seoil 계정 anaconda)의 파이썬을 가리켜 이 PC에서 작동하지 않았다.
- USB 폴더에 휴대용 파이썬 `python/`(CPython 3.13.18, python-build-standalone 20261026)을 넣고 requirements.txt 패키지를 설치했다.
- 앱은 `앱실행.bat` 또는 `python\python.exe -m streamlit run app.py`로 실행한다. PC에 파이썬 설치가 필요 없다.

## 2026-11-12 PC 파이썬 방식으로 다시 전환
- 작업할 컴퓨터에는 모두 파이썬이 설치돼 있어서, USB 휴대용 파이썬(약 900MB, USB라 느림)을 지우고 각 PC의 파이썬을 쓰기로 했다.
- 이 PC: winget으로 Python 3.13.17 설치, requirements.txt 패키지 설치 완료.
- `앱실행.bat`은 `py`(없으면 `python`)를 찾아 쓰고, 패키지가 없으면 자동 설치한다.
- 주의: Anaconda만 있고 PATH에 등록 안 된 PC에서는 파이썬을 못 찾을 수 있다. 그때는 PATH 등록 또는 bat 수정 필요.
