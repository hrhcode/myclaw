@echo off
echo 启动AI对话助手后端服务...
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
pause
