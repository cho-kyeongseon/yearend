# 연말정산 도우미

국세청 2025년 귀속 연말정산 안내 자료를 근거로 공제 여부를 안내하는 프로그램.
정적 웹페이지(`web/`)는 Vercel에 배포되고, Streamlit 앱(`app.py`)은 로컬에서 실행한다.

## 작업 규칙
- 작업 폴더는 USB이고, GitHub는 백업과 Vercel 배포용이다.
- 기본 작업 브랜치는 main. 다른 브랜치는 요청할 때만 쓴다.
- 작업이 한 단락 끝나면 HANDOFF.md를 업데이트한다.

## 참고
- GitHub: https://github.com/cho-kyeongseon/yearend (main에 푸시하면 Vercel 자동 배포)
- Vercel 사이트: https://yearend-teal.vercel.app
- 원본 자료(PDF·ZIP·HWP, `data/`)는 .gitignore로 제외돼 GitHub에 올라가지 않는다.
- 경로는 모두 `Path(__file__)` 기준 상대 경로로 쓴다. 드라이브 문자(D:, E: 등)를 코드에 적지 않는다.
- 이 폴더 자체가 저장소다. 배포 전에는 `build_web.py`로 `web/data`를 갱신한 뒤 커밋·푸시한다. (예전 `배포/` 폴더·`make_deploy.py` 방식은 없앴다)
