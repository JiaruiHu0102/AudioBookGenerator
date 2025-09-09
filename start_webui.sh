#!/bin/bash

# AudioBookGenerator-v4 Web UI 启动脚本 (Linux/Mac)

echo "============================="
echo "AudioBookGenerator-v4 Web UI"
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
python3 -c "import gradio" 2>/dev/null || {
    echo "错误: gradio 未安装"
    echo "请运行: pip install -r requirements.txt"
    exit 1
}

# 启动 Web UI
echo "启动 AudioBookGenerator-v4 Web UI..."
echo "Web UI 将在 http://127.0.0.1:9880 启动"
python3 main.py --mode webui --port 9880

echo "AudioBookGenerator-v4 Web UI 已退出" 