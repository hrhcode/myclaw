@echo off
echo Starting MyClaw Backend...
cd /d %~dp0backend
python -m pip install -e . --quiet
python -m uvicorn app.main:app --host 127.0.0.1 --port 18789 --reload
