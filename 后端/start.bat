@echo off
title 北京市文旅景点服务平台
echo ============================================
echo  北京市文旅景点服务平台 - 启动脚本
echo ============================================
echo.

:: 切换到后端目录
cd /d "%~dp0backend"

:: 检查虚拟环境
if exist "..\gis-backend\Scripts\activate.bat" (
    echo [INFO] 使用 gis-backend 虚拟环境
    call ..\gis-backend\Scripts\activate.bat
) else if exist "..\..\gis-backend\Scripts\activate.bat" (
    echo [INFO] 使用上级目录虚拟环境
    call ..\..\gis-backend\Scripts\activate.bat
) else (
    echo [WARN] 未找到 gis-backend 虚拟环境，尝试直接启动
)

:: 检查依赖是否安装
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo [INFO] 正在安装依赖...
    pip install -r requirements.txt
)

:: 检查环境配置
if not exist ".env" (
    echo [ERROR] .env 文件不存在！
    echo 请从 .env.example 复制并配置数据库和密钥信息
    pause
    exit /b 1
)

:: 启动服务
echo.
echo [INFO] 启动 FastAPI 服务...
echo [INFO] API 文档: http://localhost:8001/docs
echo [INFO] 前端页面: http://localhost:8001/app/
echo [INFO] 按 Ctrl+C 停止服务
echo.

uvicorn app:app --reload --host 0.0.0.0 --port 8001

pause
