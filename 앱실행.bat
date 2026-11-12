@echo off
chcp 65001 >nul
rem 이 컴퓨터에 설치된 파이썬으로 연말정산 도우미 앱을 실행한다.
rem 처음 실행하는 컴퓨터에서는 필요한 패키지(requirements.txt)를 자동으로 설치한다.
rem 드라이브 문자(D:, E: 등)가 바뀌어도 이 파일이 있는 폴더 기준으로 동작한다.
cd /d "%~dp0"

set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY (
  python -c "import sys" >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo [오류] 이 컴퓨터에서 파이썬을 찾을 수 없습니다.
  echo        python.org 에서 파이썬을 설치하거나, PATH에 파이썬을 등록하세요.
  pause
  exit /b 1
)

%PY% -c "import streamlit, fitz, olefile" >nul 2>nul
if errorlevel 1 (
  echo 이 컴퓨터에서 처음 실행합니다. 필요한 패키지를 설치합니다. 몇 분 걸릴 수 있습니다...
  %PY% -m pip install -r requirements.txt
  if errorlevel 1 (
    echo [오류] 패키지 설치에 실패했습니다. 인터넷 연결을 확인하세요.
    pause
    exit /b 1
  )
)

%PY% -m streamlit run app.py
pause
