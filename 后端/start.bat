@echo off
chcp 936 >nul
title 北京市文旅景点服务平台
echo ============================================
echo   北京市文旅景点服务平台 - 启动脚本
echo ============================================
echo.

cd /d "%~dp0"

if not exist ".env" (
    echo [错误] .env 文件不存在
    echo 请从 .env.example 复制一份并填写数据库密码与高德 Key
    pause
    exit /b 1
)

:: 挑选一个装了依赖的解释器：优先 PATH 里的 python，其次常见安装路径
set "PY="
python -c "import fastapi, uvicorn, aiomysql" >nul 2>&1
if not errorlevel 1 set "PY=python"
if defined PY goto HAVE_PY

if not exist "D:\anaconda\python.exe" goto NO_PY
"D:\anaconda\python.exe" -c "import fastapi, uvicorn, aiomysql" >nul 2>&1
if errorlevel 1 goto NO_PY
set "PY=D:\anaconda\python.exe"
goto HAVE_PY

:NO_PY
echo [错误] 没找到装了依赖的 Python 解释器
echo 请执行下面这行安装依赖，再重新运行本脚本：
echo    pip install -r requirements.txt
pause
exit /b 1

:HAVE_PY
echo [信息] 解释器: %PY%


echo [信息] API 文档: http://127.0.0.1:8001/docs
echo [信息] 前端页面: http://127.0.0.1:8001/app/
echo [信息] 按 Ctrl+C 停止服务
echo.
"%PY%" -m uvicorn app:app --reload --host 127.0.0.1 --port 8001
pause
