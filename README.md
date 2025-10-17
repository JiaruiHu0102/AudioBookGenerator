# AudioBookGenerator-v4 (v4.0 测试版)

基于 **GPT-SoVITS v4** 引擎的有声书生成工具

-----

## 📢 测试版特别声明 | Beta Version Notice

这是一个 **测试版本 (v4.0.x)**，主要目的是验证全新的 v4 核心引擎能否在您的计算机上稳定运行，并提供更高的音质。

-   **定位：** 它是我们未来完整版本（如 v4.1，功能更丰富）的基础。
-   **优势：** 相比于老版本，它的核心更稳定，生成的音频质量更高。
-   **功能：** 当前版本已具备核心功能，但不包含后续版本中可能新增的高级工具。

-----

## 🎯 项目简介 | Project Introduction

AudioBookGenerator-v4 是一个基于最新 GPT-SoVITS v4 引擎的有声书生成工具。我们保留了用户友好的图形界面，并将核心技术升级到 v4，为您带来更清晰、性能更强的语音生成体验。

**核心功能：**
* 将长篇小说（支持 TXT, EPUB, PDF）自动处理和分段。
* 自动识别对话角色并分配不同的声线。
* 一键生成完整的有声书音频。

-----

## ✨ 主要特性 | Key Features

### v4 核心引擎升级 | v4 Core Upgrades

| 特性 | 说明 | 效果 |
| :--- | :--- | :--- |
| **原生 48k 音质** | 生成的音频采样率提高到 48kHz。 | 比旧版的 24kHz 更清晰，消除了声音模糊感。 |
| **消除金属声** | 解决了早期版本中非整数倍上采样导致的金属声问题。 | 语音听感更自然、更舒服。 |
| **BigVGAN 技术** | 使用更先进的 BigVGAN 声码器。 | 进一步提升音频质量。 |
| **采样步数优化** | 采样步数可配置，用于平衡生成速度和语音质量。 | 您可以根据硬件情况自由调整。 |

### 继承的核心功能 | Inherited Core Features

* **简单易用：** 只需要一段 5 秒的音频样本，即可生成目标人声的语音（零样本 TTS）。
* **语言支持：** **目前仅支持中文**。
* **情感控制：** 支持多种情感表达，让语音更具表现力。
* **多话者支持：** 可自动识别并处理多角色对话场景。

-----

## 📦 安装指南 | Installation Guide

**环境要求：**
-   Python 3.9 - 3.11
-   PyTorch 2.0+
-   CUDA 11.7+ (如果您有英伟达显卡)
-   至少 8GB 内存

### 方案一：一键脚本启动（Mac/Linux 用户强烈推荐）

这个方法会使用项目自带的脚本，自动帮您创建和设置运行环境。

1.  **安装 Conda (推荐)：** 如果您还没有安装，请先安装 **Miniconda** 或 **Anaconda**。这是最稳定可靠的 Python 环境管理工具。
2.  **双击脚本：** 在项目根目录下，双击运行 `启动GUI界面.command` 文件。
    * **作用：** 脚本会自动检查、创建并激活一个名为 `audiobook-v4` 的专用环境，并使用最稳定的方式安装所有必需的依赖包。
3.  **等待：** 首次安装依赖可能需要几分钟。完成后，程序将自动启动图形界面。

### 方案二：手动安装 (推荐使用 Conda)

如果一键脚本启动遇到问题，您可以手动执行以下步骤：

1.  **克隆项目：**
    ```bash
    git clone [https://github.com/jiaruihu/AudioBookGenerator-v4.git](https://github.com/jiaruihu/AudioBookGenerator-v4.git)
    cd AudioBookGenerator-v4
    ```

2.  **创建和激活环境：**
    ```bash
    # 避免与其他项目冲突，建议创建专用环境
    conda create -n audiobook-v4 python=3.11 -y
    conda activate audiobook-v4
    ```

3.  **安装核心依赖：**

    ```bash
    # 1. 安装 PyTorch、NumPy 和 SciPy 等核心组件
    conda install pytorch torchvision torchaudio -c pytorch -y
    conda install numpy scipy -y
    
    # 2. 安装其余核心依赖
    pip install -r requirements.txt
    
    # 3. 安装 GUI 界面依赖
    conda install -c conda-forge pyqt -y
    ```

-----

## 🚀 使用方法 | Usage

### 启动应用 | Launching the Application

AudioBookGenerator-v4 提供三种启动模式:

1.  **桌面 GUI 界面（推荐）**
    ```bash
    python main.py --mode gui
    ```

2.  **Web UI 界面**
    ```bash
    python main.py --mode webui --port 9880
    ```

3.  **API 服务**
    ```bash
    python main.py --mode api --port 9880
    ```

### 快速入门步骤 | Quick Start Guide

1.  **模型与预设：** 首先进入**预设管理**页面，上传您的 GPT 模型 (`.ckpt`) 和 SoVITS 模型 (`.pth`) 文件，并至少添加一个参考音频和对应的文本。
    * **提示：** 具体模型请前往 [ModelScope](https://www.modelscope.cn/models/aihobbyist/GPT-SoVITS_Model_Collection/files) 自行下载。
2.  **处理文本：** 返回主界面，选择您的文本文件（支持 TXT/EPUB/PDF），设置好处理字数和是否进行**多人朗读**模式。
3.  **分段与配音：**
    * **单人模式：** 进入**单段处理**页面，选择预设，试听或直接生成。
    * **多人模式：** 会先进入**角色统计**页面，您可以为主要角色分配预设，然后进入**分段处理**页面，微调每个段落的配音和情绪。
4.  **生成全书：** 点击**一键生成所有**或**生成全书**按钮，程序将自动批量生成并合并音频文件。

-----

## 📁 项目结构 | Project Structure

AudioBookGenerator-v4/ ├── main.py # 主启动脚本 | Main launch script ├── gpt_sovits.py # GPT-SoVITS v4 适配器 | GPT-SoVITS v4 adapter ├── ui_main.py # 主界面 | Main GUI ├── preset_manager.py # 预设管理器 | Preset manager ├── text_processor.py # 文本处理器 | Text processor ├── requirements.txt # Python依赖 | Python dependencies ├── requirements_ui.txt # UI依赖 | UI dependencies ├── presets/ # 预设文件 | Preset files ├── Working/ # 工作目录（处理结果和中间文件） | Working directory └── output_audio/ # 最终输出音频 | Output audio

-----

## 🔧 故障排除 | Troubleshooting

1.  **模型加载失败：** 请检查模型文件路径是否正确；如果使用 Conda，请确保环境已激活；并确认内存/显存是否充足 [cite: 3]。
2.  **音频生成失败：** 检查参考音频文件是否存在且格式正确；如果是 GPU 用户，请检查显存是否足够 [cite: 3]。
3.  **性能优化：** 如果生成速度慢，请考虑安装 CUDA 版本的 PyTorch 并启用 GPU，或尝试在预设中减少“采样步数”参数 [cite: 3]。

-----

## 🙏 致谢 | Acknowledgements

* [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) - 核心 TTS 技术 [cite: 3]
* [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - GUI 界面框架 [cite: 3]
* B站白菜工厂1145号员工训练的大量模型以及收集的参考音频，感谢！ [cite: 3]
* 感谢所有为本项目提供 Bug 报告和功能建议的朋友们 [cite: 3]！

-----

## 📞 联系我们 | Contact Us

如果您有任何问题或建议，请通过以下方式联系我们：

* **📧 Email:** jiaruihu2001@gmail.com
* **💻 B站:** Jaceow
* **📕 小红书:** JadeH
