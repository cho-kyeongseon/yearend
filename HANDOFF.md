# HANDOFF

> 마지막 업데이트: 2026-11-12 (작업 마무리)

## 현재 상태
- USB의 `연말정산` 폴더 = GitHub `cho-kyeongseon/yearend`(공개 저장소)의 main 브랜치. 커밋할 변경 없이 깨끗한 상태.
- main에 푸시하면 Vercel이 자동 배포한다. 사이트: https://yearend-teal.vercel.app (최근 배포 모두 성공)
- Streamlit 앱(`app.py`)은 이 PC의 파이썬으로 실행 확인함. 서버 4~6초, 화면 3초. 빠른 질문 "월세 세액공제" 답변 정상.
- `build_web.py` 정상 동작 (항목 14개, FAQ 36개).
- 알려진 오류: 없음.

## 실행 방법
- 준비물: 작업하는 컴퓨터에 파이썬 3.13 이상(`py` 또는 `python`으로 실행 가능해야 함), 인터넷(처음 한 번 패키지 설치).
- 앱 실행: `앱실행.bat` 더블클릭. 패키지(streamlit, pymupdf, olefile)가 없으면 자동 설치 후 실행한다.
  - 직접 실행: `py -m streamlit run app.py`
- 패키지만 설치: `py -m pip install -r requirements.txt`
- 웹 데이터 갱신(배포 전): `py build_web.py` → 커밋 → main 푸시
- 자료 다시 색인(새 연도 자료): `py ingest.py` → `py build_web.py` → 커밋 → main 푸시
- 자세한 절차는 배포안내.md 참고.

## 원본 자료 위치 (GitHub에 없음, USB에만 있음)
프로그램은 모두 작업 폴더 기준 상대 경로(`Path(__file__)`)로 읽으므로 드라이브 문자와 무관하다.

| 자료 | 위치 (작업 폴더 기준) | 읽는 프로그램 |
|---|---|---|
| 국세청 안내 PDF 3개, HWP 2개, ZIP 2개 (약 21MB) | 폴더 바로 아래 `*.pdf`, `*.hwp`, `*.zip` | `ingest.py` |
| ZIP 압축 해제본 (약 23MB) | `data/extracted/` | `ingest.py` (ZIP에서 자동 생성) |
| 검색용 색인 (GitHub에 있음) | `index/chunks.json` → `web/data/chunks.json` | `rag.py`, `bot.py`, `build_web.py` |

- 원본 파일 목록: 2025년 원천징수의무자를 위한 신고안내.pdf, 연말정산 주택자금·월세액 공제의 이해(2025년)_수정반영.pdf, 중소기업 취업자 소득세 감면제도 안내(2025년).pdf, 2026년 연말정산 관련 개정세법 요약.hwp, 간소화자료 일괄제공 서비스 설명 자료(배포용).hwp, 2025년 연말정산 주요서식 모음(개정안 포함).zip, 2025년 원천징수의무자를 위한 연말정산 신고안내_26.02.03..zip
- `.gitignore`로 `*.pdf`, `*.zip`, `*.hwp`, `data/`, `.venv/`, `python/` 등을 제외한다. USB를 잃어버리면 원본 자료는 복구할 수 없으니 따로 백업해 둘 것.

## 남은 일
- 다른 PC(이전 PC 포함)에서 `앱실행.bat` 첫 실행(패키지 자동 설치)을 아직 실제로 해 보지 않았다.
- Anaconda만 있고 PATH에 등록 안 된 PC에서는 `앱실행.bat`이 파이썬을 못 찾는다. 그런 PC를 쓰게 되면 bat에 Anaconda 경로 찾기를 추가한다.

## 주의할 점
- GitHub 저장소는 **공개**다. 커밋하는 파일에 개인정보·계정 이름·비밀값을 넣지 않는다. (이전 커밋 6d0cfd1, 3eef413에 이전 PC 계정 이름이 남아 있지만 그대로 두기로 했다)
- USB는 Git이 파일 소유자를 확인하지 못해서, 새 PC나 드라이브 문자가 바뀐 경우 처음 한 번 `git config --global --add safe.directory <작업 폴더 경로>`가 필요하다.
- USB에 .venv나 휴대용 파이썬을 두지 않는다(절대 경로에 묶이거나, 크고 느림).
- 기본 브랜치는 main. 다른 브랜치는 요청할 때만 쓴다.

---

# 작업 기록

## 2026-11-12 저장소 연결
- USB 작업 폴더(연말정산) 자체를 GitHub `cho-kyeongseon/yearend`(main)에 연결했다.
- 로컬에만 있던 소스(app.py, bot.py, ingest.py, rag.py, make_deploy.py, 배포안내.md, .claude/launch.json)를 저장소에 추가했다.
- .gitignore로 원본 자료(PDF·ZIP·HWP, data/), .venv, `배포/` 폴더를 제외했다.
- Vercel 프로젝트는 이미 연결돼 있었다: https://yearend-teal.vercel.app

## 2026-11-12 배포 방식 정리
- `배포/` 폴더(옛 GitHub 업로드용 복사본)와 `make_deploy.py`를 삭제했다. 내용은 모두 GitHub 첫 커밋(a0c3349)에 남아 있다.
- 배포안내.md를 새 방식(USB 폴더에서 `build_web.py` 실행 → main 푸시 → Vercel 자동 배포)으로 고쳐 썼다.

## 2026-11-12 USB 휴대용 파이썬으로 전환
- 기존 .venv는 다른 PC(이전 PC의 Anaconda)의 파이썬을 가리켜 이 PC에서 작동하지 않았다.
- USB 폴더에 휴대용 파이썬 `python/`(CPython 3.13.18, python-build-standalone 20261026)을 넣고 requirements.txt 패키지를 설치했다.
- 앱은 `앱실행.bat` 또는 `python\python.exe -m streamlit run app.py`로 실행한다. PC에 파이썬 설치가 필요 없다.

## 2026-11-12 PC 파이썬 방식으로 다시 전환
- 작업할 컴퓨터에는 모두 파이썬이 설치돼 있어서, USB 휴대용 파이썬(약 900MB, USB라 느림)을 지우고 각 PC의 파이썬을 쓰기로 했다.
- 이 PC: winget으로 Python 3.13.17 설치, requirements.txt 패키지 설치 완료.
- `앱실행.bat`은 `py`(없으면 `python`)를 찾아 쓰고, 패키지가 없으면 자동 설치한다.
- 주의: Anaconda만 있고 PATH에 등록 안 된 PC에서는 파이썬을 못 찾을 수 있다. 그때는 PATH 등록 또는 bat 수정 필요.

## PC별 파이썬 환경 (2026-11-12 기준)

### 이 PC (Windows 11 Home)
| 항목 | 내용 |
|---|---|
| 파이썬 | Python 3.13.17 (64-bit) |
| 설치 방법 | winget `Python.Python.3.13`, 현재 사용자 전용 설치(`--scope user`) |
| 설치 위치 | `%LOCALAPPDATA%\Programs\Python\Python313\` (약 660MB, 패키지 포함) |
| 실행 파일 | `...\Python313\python.exe` |
| py 런처 | `%LOCALAPPDATA%\Programs\Python\Launcher\py.exe` (Python Launcher 3.14.7, `py --list` → 3.13만 있음) |
| PATH(사용자) | `...\Python313\Scripts\`, `...\Python313\`, `...\Python\Launcher\` 등록됨 |
| pip | 26.2.2 |
| 프로젝트 패키지 | streamlit 1.67.0, pymupdf 2.1, olefile 0.47 (가상환경 없이 이 파이썬에 직접 설치, 의존 패키지 포함 45개) |
| 확인 결과 | 앱 서버 4~6초, 화면 표시 3초 |

- 이 컴퓨터에서는 `py`, `python` 둘 다 위 파이썬을 가리킨다. (단, 설치 전에 열려 있던 창·프로그램은 다시 열어야 PATH가 반영된다)
- 제거하려면: Windows 설정 → 앱 → 설치된 앱에서 "Python 3.13.17 (64-bit)", "Python Launcher" 제거.

### 이전 PC
- Anaconda 파이썬 3.13.9, `%USERPROFILE%\anaconda3\python.exe`
- 처음 .venv를 이 파이썬으로 만들었다(현재는 삭제됨). 이 PC에서 `앱실행.bat`이 파이썬을 못 찾으면 Anaconda를 PATH에 등록하거나 bat에 Anaconda 경로 찾기를 추가해야 한다.
- 이 PC에 프로젝트 패키지가 설치돼 있는지는 아직 확인하지 않았다. 처음 `앱실행.bat`을 실행하면 자동 설치된다.
