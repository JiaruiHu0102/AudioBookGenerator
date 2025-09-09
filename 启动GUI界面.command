#!/bin/bash

# AudioBookGenerator-v4 GUI 启动脚本 (macOS .command 文件)
# 双击此文件即可启动 GUI 界面

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# 切换到项目目录
cd "$SCRIPT_DIR"

echo "=========================================="
echo "     AudioBookGenerator-v4 GUI 启动器"
echo "=========================================="
echo "项目目录: $SCRIPT_DIR"
echo ""

# 检查 conda 环境
if command -v conda &> /dev/null; then
    echo "✅ 发现 Conda 环境: $(conda --version)"
    
    # 检查是否存在专用环境
    if conda env list | grep -q "audiobook-v4"; then
        echo "🔄 激活现有 audiobook-v4 环境..."
        source $(conda info --base)/etc/profile.d/conda.sh
        conda activate audiobook-v4
        echo "✅ Conda 环境已激活"
    else
        echo "🆕 创建 audiobook-v4 环境..."
        source $(conda info --base)/etc/profile.d/conda.sh
        conda create -n audiobook-v4 python=3.11 -y
        conda activate audiobook-v4
        echo "✅ 新的 Conda 环境已创建并激活"
    fi
    
    # 使用 conda 的 python
    PYTHON_CMD="python"
elif [ -d "venv" ]; then
    echo "🔄 激活虚拟环境..."
    source venv/bin/activate
    echo "✅ 虚拟环境已激活"
    PYTHON_CMD="python3"
elif command -v python3 &> /dev/null; then
    echo "⚠️  未找到 Conda 或虚拟环境，使用系统 Python"
    echo "💡 建议安装 miniconda 获得更好的体验: https://docs.conda.io/en/latest/miniconda.html"
    echo ""
    echo "是否创建虚拟环境? (y/n): "
    read -r create_venv
    if [[ $create_venv =~ ^[Yy]$ ]]; then
        echo "🆕 创建虚拟环境..."
        python3 -m venv venv
        source venv/bin/activate
        echo "✅ 虚拟环境已创建并激活"
    fi
    PYTHON_CMD="python3"
else
    echo "❌ 错误: 未找到 Python3 或 Conda"
    echo "请安装以下任一选项:"
    echo "1. Miniconda (推荐): https://docs.conda.io/en/latest/miniconda.html"
    echo "2. Python 3.9+: brew install python@3.11"
    echo ""
    echo "按回车键退出..."
    read
    exit 1
fi

echo "✅ Python 版本: $($PYTHON_CMD --version)"

# 检查依赖
echo "🔍 检查 UI 依赖..."
$PYTHON_CMD -c "import PyQt6" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ PyQt6 已安装"
else
    echo "❌ PyQt6 未安装"
    echo "正在安装 UI 依赖..."
    
    if command -v conda &> /dev/null && [[ "$CONDA_DEFAULT_ENV" == "audiobook-v4" ]]; then
        # 优先使用 conda 安装
        conda install pyqt -y
        pip install -r requirements_ui.txt
    else
        pip install -r requirements_ui.txt
    fi
    
    if [ $? -eq 0 ]; then
        echo "✅ UI 依赖安装成功"
    else
        echo "❌ UI 依赖安装失败"
        echo "请手动运行: pip install -r requirements_ui.txt"
        echo ""
        echo "按回车键退出..."
        read
        exit 1
    fi
fi

# 检查核心依赖
echo "🔍 检查核心依赖..."
$PYTHON_CMD -c "import torch, numpy, jieba" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ 核心依赖已安装"
else
    echo "❌ 核心依赖未安装"
    echo "正在安装核心依赖 (这可能需要几分钟)..."
    
    if command -v conda &> /dev/null && [[ "$CONDA_DEFAULT_ENV" == "audiobook-v4" ]]; then
        # 使用 conda 安装主要依赖，避免编译问题
        echo "📦 使用 Conda 安装核心依赖..."
        conda install pytorch torchvision torchaudio -c pytorch -y
        conda install numpy scipy -y
        
        # 安装其他依赖，跳过问题包
        echo "📦 安装其他依赖 (跳过可能有问题的包)..."
        pip install jieba gradio fastapi uvicorn
        pip install librosa soundfile
        
        # 单独处理可能有问题的包
        echo "📦 尝试安装可选依赖..."
        pip install pyopenjtalk --timeout 300 || echo "⚠️  pyopenjtalk 安装失败，将跳过 (不影响中文语音合成)"
        pip install opencc || echo "⚠️  opencc 安装失败，将跳过"
        
        # 安装剩余依赖
        pip install -r requirements.txt --timeout 300 || echo "⚠️  部分依赖安装失败，但核心功能应该可用"
    else
        # 使用 pip 安装，但增加超时和错误处理
        echo "📦 使用 pip 安装依赖..."
        pip install torch torchvision torchaudio numpy scipy jieba gradio fastapi uvicorn librosa soundfile --timeout 600
        
        # 尝试安装剩余依赖，允许部分失败
        pip install -r requirements.txt --timeout 600 || echo "⚠️  部分依赖安装失败，但核心功能应该可用"
    fi
    
    # 再次检查核心依赖
    $PYTHON_CMD -c "import torch, numpy, jieba" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✅ 核心依赖安装成功"
    else
        echo "❌ 核心依赖安装失败"
        echo "请检查网络连接或手动安装:"
        echo "1. conda install pytorch -c pytorch"
        echo "2. pip install torch numpy jieba"
        echo ""
        echo "按回车键退出..."
        read
        exit 1
    fi
fi

echo ""
echo "🚀 启动 AudioBookGenerator-v4 GUI..."
echo "正在加载，请稍候..."
echo ""

# 启动 GUI
$PYTHON_CMD main.py --mode gui

echo ""
echo "🔚 AudioBookGenerator-v4 GUI 已退出"
echo "按回车键关闭此窗口..."
read 