# AI对话助手 - 一键启动脚本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   AI对话助手 - 一键启动" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 启动后端服务
Write-Host "正在启动后端服务..." -ForegroundColor Yellow
$backendJob = Start-Job -ScriptBlock {
    Set-Location backend
    python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
} -Name "BackendService"

# 等待后端服务启动
Write-Host "等待后端服务启动..." -ForegroundColor Gray
Start-Sleep -Seconds 3

# 启动前端服务
Write-Host "正在启动前端服务..." -ForegroundColor Yellow
$frontendJob = Start-Job -ScriptBlock {
    Set-Location frontend
    npm run dev
} -Name "FrontendService"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   服务启动完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "后端服务: http://localhost:8000" -ForegroundColor White
Write-Host "前端服务: http://localhost:5173" -ForegroundColor White
Write-Host "API文档:   http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "按 Ctrl+C 停止所有服务" -ForegroundColor Yellow

# 等待用户中断
try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
} finally {
    Write-Host ""
    Write-Host "正在停止服务..." -ForegroundColor Yellow
    Stop-Job -Name "BackendService" -Force
    Stop-Job -Name "FrontendService" -Force
    Remove-Job -Name "BackendService" -Force
    Remove-Job -Name "FrontendService" -Force
    Write-Host "服务已停止" -ForegroundColor Red
}
