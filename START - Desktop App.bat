@echo off
title YouTube Downloader Desktop
color 0a
echo.
echo  ==========================================
echo    YouTube Downloader Desktop App
echo  ==========================================
echo.

:: Check Node.js
where node >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found!
    echo Download from: https://nodejs.org
    pause
    exit /b
)

:: Install dependencies if needed
if not exist "node_modules" (
    echo Installing Electron...
    npm install
)

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    pause
    exit /b
)

echo Starting YouTube Downloader Desktop App...
echo.
npm start
