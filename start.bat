@echo off
chcp 65001 >nul
title SmartPlan 时间规划助手

echo ============================================
echo    SmartPlan 时间规划助手 - 一键启动
echo ============================================
echo.

cd /d "%~dp0"

:: 1. 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3
    pause
    exit /b 1
)
echo [1/3] Python 已就绪

:: 2. 创建虚拟环境 & 安装依赖（仅首次）
if not exist "venv\Scripts\python.exe" (
    echo [2/3] 首次运行，正在创建虚拟环境...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    echo [2/3] 依赖已就绪
    call venv\Scripts\activate.bat
)

:: 3. 启动应用（自动初始化数据库）
echo [3/3] 启动应用...
echo.
python app.py

pause
