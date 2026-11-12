@echo off
chcp 65001 >nul
rem USB 안의 휴대용 파이썬(python\)으로 연말정산 도우미 앱을 실행한다.
rem 드라이브 문자(D:, E: 등)가 바뀌어도 이 파일이 있는 폴더 기준으로 동작한다.
cd /d "%~dp0"
if not exist "python\python.exe" (
  echo [오류] python\python.exe 가 없습니다. 휴대용 파이썬 폴더를 확인하세요.
  pause
  exit /b 1
)
"python\python.exe" -m streamlit run app.py
pause
