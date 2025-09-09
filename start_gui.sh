#!/bin/bash

# AudioBookGenerator-v4 GUI 启动脚本 (Linux/Mac)

echo "============================="
echo "AudioBookGenerator-v4 GUI"
echo "============================="

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python3"
    exit 1
fi

# 检查虚拟环境
if [ -d "venv" ]; then
    echo "激活虚拟环境..."
    source venv/bin/activate
fi

# 检查依赖
echo "检查依赖..."
python3 -c "import PyQt6" 2>/dev/null || {
    echo "错误: PyQt6 未安装"
    echo "请运行: pip install -r requirements_ui.txt"
    exit 1
}

# 启动 GUI
echo "启动 AudioBookGenerator-v4 GUI..."
python3 main.py --mode gui

echo "AudioBookGenerator-v4 GUI 已退出" 