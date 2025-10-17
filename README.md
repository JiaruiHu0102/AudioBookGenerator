# AudioBookGenerator-v4

基于 GPT-SoVITS v4 版本的有声书生成器

-----

## 🎯 项目简介 | Project Introduction

AudioBookGenerator-v4 是一个基于 GPT-SoVITS v4 版本的有声书生成器，它继承了原始 GPT-SoVITS-App 的所有 UI 设计和功能，同时升级到了 v4 版本的 GPT-SoVITS 核心，享受更高的音频质量和更强的性能。

**AudioBookGenerator-v4** is an audiobook generator built on the GPT-SoVITS v4 core. It inherits all the UI design and features of the original GPT-SoVITS-App while upgrading to the v4 core for higher audio quality and stronger performance.

-----

## ✨ 主要特性 | Key Features

### v4 版本升级特性 | v4 Core Upgrades

  - **原生 48k 音频输出 | Native 48k Audio Output**: Compared to the v3 version's 24k, the audio quality is clearer, avoiding a muffled sound.
  - **修复金属声问题 | Fixes for Metallic Sound**: Solves the metallic sound issue from the v3 version caused by non-integer upsampling.
  - **BigVGAN 声码器 | BigVGAN Vocoder**: Utilizes the more advanced BigVGAN vocoder for better audio quality.
  - **音频超分辨率 | Audio Super-Resolution**: Optional audio super-resolution feature to further enhance audio quality.
  - **优化的采样步数 | Optimized Sample Steps**: Configurable sample steps to balance quality and speed.

### 继承的功能特性 | Inherited Features

  - **零样本 TTS | Zero-Shot TTS**: Generate instant text-to-speech with a 5-second voice sample.
  - **少样本 TTS | Few-Shot TTS**: Fine-tune with just 1 minute of training data to improve voice similarity and realism.
  - **多语言支持 | Multi-language Support**: Supports multiple languages, including Chinese, English, Japanese, Korean, and Cantonese.
  - **情感控制 | Emotion Control**: Supports various emotional expressions to make the voice more expressive.
  - **多话者支持 | Multi-Speaker Support**: Automatically identifies and handles multi-speaker scenarios.
  - **批量处理 | Batch Processing**: Supports automatic text segmentation and batch generation for long texts.

-----

## 📦 安装指南 | Installation Guide

### 环境要求 | Prerequisites

  - Python 3.9 - 3.11
  - PyTorch 2.0+
  - CUDA 11.7+ (for GPU users)
  - 8GB+ RAM
  - 10GB+ Free Storage

### 安装步骤 | Installation Steps

#### 方案一：使用 Conda (推荐) | Option 1: Using Conda (Recommended)

1.  **安装 Miniconda | Install Miniconda**

<!-- end list -->

```bash
# macOS users
brew install --cask miniconda

# Or download from the official website: https://docs.conda.io/en/latest/miniconda.html
```

2.  **一键安装环境 | One-Click Environment Setup**

<!-- end list -->

```bash
# macOS users: double-click "安装conda环境.command"
# Or manually execute:
conda create -n audibook-v4 python=3.11 -y
conda activate audibook-v4
pip install -r requirements.txt
pip install -r requirements_ui.txt
# For GPU users, install PyTorch with CUDA support:
# conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia -y
```

#### 方案二：使用虚拟环境 | Option 2: Using a Virtual Environment

1.  **克隆项目 | Clone the Project**

<!-- end list -->

```bash
git clone https://github.com/jiaruihu/AudioBookGenerator-v4.git
cd AudioBookGenerator-v4
```

2.  **创建虚拟环境 | Create a Virtual Environment**

<!-- end list -->

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# Or
venv\Scripts\activate  # Windows
```

3.  **安装依赖 | Install Dependencies**

<!-- end list -->

```bash
pip install -r requirements.txt
pip install -r requirements_ui.txt
```

-----

## 🚀 使用方法 | Usage

### 启动应用 | Launching the Application

AudioBookGenerator-v4 provides three launch modes:

#### 1\. 桌面 GUI 界面（推荐） | Desktop GUI (Recommended)

```bash
python main.py --mode gui
```

#### 2\. Web UI 界面 | Web UI

```bash
python main.py --mode webui --port 9880
```

#### 3\. API 服务 | API Service

```bash
python main.py --mode api --port 9880
```

### 快速启动脚本 | Quick Start Scripts

**Windows 用户 | Windows Users**

```bash
# Double-click to run
start_gui.bat
start_webui.bat
start_api.bat
```

**Linux/Mac 用户 | Linux/Mac Users**

```bash
# Run in terminal
./start_gui.sh
./start_webui.sh
./start_api.sh
```

**macOS 用户 (推荐) | macOS Users (Recommended)**

```bash
# Double-click to run (easier)
安装conda环境.command    # 🆕 First time, install the environment
启动GUI界面.command      # Launch the desktop GUI
启动WebUI界面.command    # Launch the Web UI
启动API服务.command      # Launch the API service
```

-----

## 📖 使用教程 | User Guide

### 1\. 预设管理 | Preset Management

AudioBookGenerator-v4 uses a preset system to manage different voice roles:

1.  **创建预设 | Create a Preset**

      - Select the GPT model file (`.ckpt`).
      - Select the SoVITS model file (`.pth`).
      - Upload a reference audio file.
      - Enter the text content of the reference audio.
      - Configure language and emotion parameters.
      - 具体模型请前往https://www.modelscope.cn/models/aihobbyist/GPT-SoVITS_Model_Collection/files自行下载

3.  **管理预设 | Manage Presets**

      - Select, edit, or delete presets from the preset list.
      - Presets are automatically saved to the `presets/` directory.

### 2\. 文本处理 | Text Processing

1.  **加载文本文件 | Load a Text File**

      - Supports `.txt`, `.epub`, and `.pdf` file formats.
      - Automatically converts `.epub` and `.pdf` files to `.txt`.

2.  **文本分段 | Text Segmentation**

      - Automatically segments text based on punctuation.
      - Supports manual adjustment of the segmented result.

3.  **多话者处理 | Multi-Speaker Processing**

      - Automatically identifies different roles in dialogue.
      - Assigns a different preset to each role.

### 3\. 音频生成 | Audio Generation

1.  **预览生成 | Generate Preview**

      - Select a text segment.
      - Click the "Generate Preview" button.
      - Play the preview audio.

2.  **批量生成 | Batch Generation**

      - After configuring all presets, click the "Generate All" button.
      - Wait for the batch generation to complete.

3.  **音频合并 | Audio Merging**

      - Automatically merges the generated audio clips.
      - Outputs a complete audiobook file.

-----

## ⚙️ 配置说明 | Configuration

### v4 版本特有配置 | v4 Core Configuration

You can adjust the following v4-specific parameters in the `config.py` file:

```python
class V4Config:
    """v4版本特有配置"""
    
    # v4版本默认参数
    DEFAULT_SAMPLE_STEPS = 32
    DEFAULT_IF_SR = False
    DEFAULT_NATIVE_48K = True
    DEFAULT_BIGVGAN_ENABLED = True
    
    # v4版本推荐参数值
    RECOMMENDED_PARAMS = {
        'temperature': 1.0,
        'top_k': 15,
        'top_p': 1.0,
        'repetition_penalty': 1.35,
        'sample_steps': 32,
        'if_sr': False,
        'speed_factor': 1.0,
        'fragment_interval': 0.3,
        'batch_size': 1,
        'text_lang': 'all_zh',
    }
```

### 情感控制配置 | Emotion Control Configuration

The application's emotion control relies on the `GPT-SoVITS` core. The emotional parameters are managed within the preset configuration, allowing for flexible emotion settings for different voices.

-----

## 📁 项目结构 | Project Structure

```
AudioBookGenerator-v4/
├── main.py                 # 主启动脚本 | Main launch script
├── gpt_sovits.py          # GPT-SoVITS v4 适配器 | GPT-SoVITS v4 adapter
├── ui_main.py             # 主界面 | Main GUI
├── preset_manager.py      # 预设管理器 | Preset manager
├── text_processor.py      # 文本处理器 | Text processor
├── config.py              # 配置文件 | Configuration file
├── requirements.txt       # Python依赖 | Python dependencies
├── requirements_ui.txt    # UI依赖 | UI dependencies
├── GPT_SoVITS/           # GPT-SoVITS v4 核心 | GPT-SoVITS v4 core
├── tools/                 # 工具模块 | Tool modules
├── presets/              # 预设文件 | Preset files
├── Working/              # 工作目录 | Working directory
├── output_audio/         # 输出音频 | Output audio
├── preview_audio/        # 预览音频 | Preview audio
└── README.md             # 说明文档 | Documentation
```

-----

## 🔧 故障排除 | Troubleshooting

### 常见问题 | Common Issues

1.  **模型加载失败 | Model Loading Failed**

      - Check if the model file paths are correct.
      - Verify the integrity of the model files.
      - Ensure you have sufficient memory.

2.  **音频生成失败 | Audio Generation Failed**

      - Check if the reference audio file exists.
      - Verify the sample rate and format of the reference audio.
      - Ensure you have sufficient GPU memory.

3.  **UI 界面启动失败 | UI Launch Failed**

      - Check if PyQt6 is installed correctly.
      - Verify Python version compatibility.
      - Check the error logs for details.

### 性能优化 | Performance Optimization

1.  **GPU 加速 | GPU Acceleration**

      - Install the CUDA version of PyTorch.
      - Enable the GPU device in the configuration.
      - Monitor GPU memory usage.

2.  **内存优化 | Memory Optimization**

      - Enable half-precision floating-point numbers.
      - Reduce the batch size.
      - Release unused models promptly.

-----

## 🤝 贡献指南 | Contribution Guide

We welcome all forms of contributions, including but not limited to:

  - 🐛 Bug reports
  - 💡 Feature suggestions
  - 📝 Documentation improvements
  - 🔧 Code contributions

-----

## 📄 许可证 | License

This project is licensed under the MIT License. For more details, see the [LICENSE](https://www.google.com/search?q=LICENSE) file.

-----

## 🙏 致谢 | Acknowledgements

  - [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) - Core TTS technology
  - [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - GUI framework
  - [BigVGAN](https://github.com/NVIDIA/BigVGAN) - Vocoder technology
  - B站白菜工厂1145号员工训练的大量模型以及收集的参考音频，感谢！

-----

## 📞 联系我们 | Contact Us

If you have any questions or suggestions, please contact us at:

  - 📧 Email: jiaruihu2001@gmail.com

