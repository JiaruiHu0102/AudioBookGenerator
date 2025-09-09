@echo off
REM AudioBookGenerator-v4 Web UI 启动脚本 (Windows)

echo =============================
echo AudioBookGenerator-v4 Web UI
echo =============================

REM 检查 Python 环境
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到 Python
    pause
    exit /b 1
)

REM 检查虚拟环境
if exist "venv" (
    echo 激活虚拟环境...
    call venv\Scripts\activate
)

REM 检查依赖
echo 检查依赖...
python -c "import gradio" 2>nul
if %errorlevel% neq 0 (
    echo 错误: gradio 未安装
    echo 请运行: pip install -r requirements.txt
    pause
    exit /b 1
)

REM 启动 Web UI
echo 启动 AudioBookGenerator-v4 Web UI...
echo Web UI 将在 http://127.0.0.1:9880 启动
python main.py --mode webui --port 9880

echo AudioBookGenerator-v4 Web UI 已退出
pause 