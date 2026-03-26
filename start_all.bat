@echo off
chcp 65001 >nul
echo ========================================
echo    AI对话助手 - 一键启动
echo ========================================
echo.

echo 正在启动后端服务...
start "后端服务" cmd /k "cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

echo 等待后端服务启动...
timeout /t 3 /nobreak >nul

echo 正在启动前端服务...
start "前端服务" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo    服务启动完成！
echo ========================================
echo.
echo 后端服务: http://localhost:8000
echo 前端服务: http://localhost:5173
echo API文档: http://localhost:8000/docs
echo.
echo 按任意键关闭此窗口（服务将继续运行）...
pause >nul
