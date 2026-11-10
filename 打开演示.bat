@echo off
chcp 936 >nul
title 北京文旅平台 - 一键演示

for /d %%i in ("%~dp0*") do if exist "%%i\app.py" set "BE=%%i"
if not defined BE (
    echo [错误] 没找到后端目录，请确认 app.py 存在
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


netstat -ano | findstr ":8001" | findstr "LISTENING" >nul
if not errorlevel 1 goto OPEN

echo.
echo   正在启动服务，约 8 秒后浏览器自动打开
echo   本窗口就是服务窗口，演示结束直接关掉它即可
echo   前端  http://127.0.0.1:8001/app/
echo   文档  http://127.0.0.1:8001/docs
echo.

start "" /min "%PY%" -c "import time,webbrowser as w; time.sleep(8); w.open('http://127.0.0.1:8001/app/')"

cd /d "%BE%"
"%PY%" -m uvicorn app:app --port 8001

echo.
echo   服务已停止。若上方有红色报错，先确认 MySQL 已启动、.env 里密码正确。
pause
exit /b 0

:OPEN
echo.
echo   检测到服务已在运行，直接打开浏览器
echo   前端  http://127.0.0.1:8001/app/
echo   文档  http://127.0.0.1:8001/docs
echo.
start "" "http://127.0.0.1:8001/app/"
pause
exit /b 0
