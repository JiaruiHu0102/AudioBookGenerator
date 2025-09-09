@echo off
REM AudioBookGenerator-v4 GUI 启动脚本 (Windows)

echo =============================
echo AudioBookGenerator-v4 GUI
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
python -c "import PyQt6" 2>nul
if %errorlevel% neq 0 (
    echo 错误: PyQt6 未安装
    echo 请运行: pip install -r requirements_ui.txt
    pause
    exit /b 1
)

REM 启动 GUI
echo 启动 AudioBookGenerator-v4 GUI...
python main.py --mode gui

echo AudioBookGenerator-v4 GUI 已退出
pause 