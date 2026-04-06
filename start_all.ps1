# MyClaw - 一键启动脚本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   MyClaw - One-Click Start" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$projectRoot = $PSScriptRoot

# 启动后端
Write-Host "启动后端服务..." -ForegroundColor Yellow
$backendProcess = Start-Process -FilePath "python" -ArgumentList "start_server.py" -WorkingDirectory "$projectRoot\backend" -PassThru -WindowStyle Normal

# 等待后端启动
Write-Host "等待后端启动..." -ForegroundColor Gray
Start-Sleep -Seconds 4

# 启动前端
Write-Host "启动前端服务..." -ForegroundColor Yellow
$frontendProcess = Start-Process -FilePath "npm" -ArgumentList "run dev" -WorkingDirectory "$projectRoot\frontend" -PassThru -WindowStyle Normal

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   服务已启动!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "后端:  http://localhost:8000" -ForegroundColor White
Write-Host "前端:  http://localhost:5173" -ForegroundColor White
Write-Host "API文档: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "按任意键停止所有服务..." -ForegroundColor Yellow

# 等待用户按键
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# 停止服务
Write-Host ""
Write-Host "正在停止服务..." -ForegroundColor Yellow
Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
Stop-Process -Id $frontendProcess.Id -Force -ErrorAction SilentlyContinue
Write-Host "服务已停止" -ForegroundColor Red
