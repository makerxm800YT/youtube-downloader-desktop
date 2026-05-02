@echo off
title YouTube Downloader Desktop
color 0a
echo.
echo ==========================================
echo   YouTube Downloader Desktop App
echo ==========================================
echo.

where node >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found!
    echo Download from: https://nodejs.org
    pause
    exit /b
)

if not exist "node_modules" (
    echo Installing Electron...
    npm install
)

echo Starting...
npm start
