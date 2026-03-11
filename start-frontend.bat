@echo off
echo Starting MyClaw Frontend...
cd /d %~dp0frontend
call npm install
call npm run dev
