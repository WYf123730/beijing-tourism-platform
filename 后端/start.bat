@echo off
chcp 65001 >nul
title 北京市文旅景点服务平台
echo ============================================
echo   北京市文旅景点服务平台 - 启动脚本
echo ============================================
echo.

:: 本脚本就在后端目录，直接在此运行
cd /d "%~dp0"

:: 检查环境配置
if not exist ".env" (
    echo [ERROR] .env 文件不存在
    echo 请从 .env.example 复制一份并填写数据库密码与高德 Key
    pause
    exit /b 1
)

:: 选择解释器：优先 PATH 里的 python，否则用 Anaconda
where python >nul 2>&1
if errorlevel 1 (
    set "PY=D:\anaconda\python.exe"
) else (
    set "PY=python"
)

:: 检查依赖是否安装
"%PY%" -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo [INFO] 缺少依赖，正在安装...
    "%PY%" -m pip install -r requirements.txt
)

:: 启动服务
echo [INFO] 使用解释器: %PY%
echo [INFO] API 文档: http://127.0.0.1:8001/docs
echo [INFO] 前端页面: http://127.0.0.1:8001/app/
echo [INFO] 按 Ctrl+C 停止服务
echo.

"%PY%" -m uvicorn app:app --reload --host 127.0.0.1 --port 8001

pause
