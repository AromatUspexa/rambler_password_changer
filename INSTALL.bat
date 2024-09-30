@echo off
python -m venv .venv
call .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
@echo To start the script run "START.bat"
pause