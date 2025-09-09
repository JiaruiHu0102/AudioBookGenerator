#!/usr/bin/env python3
"""
AudioBookGenerator-v4 主启动脚本
基于 GPT-SoVITS v4 版本的有声书生成器
"""

import sys
import os
import argparse
from pathlib import Path
import logging

# 设置项目根目录
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / 'app.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def check_dependencies():
    """检查必要的依赖项"""
    required_modules = [
        'torch',
        'PyQt6',
        'numpy',
        'soundfile',
        'jieba',
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        logger.error(f"缺少以下依赖项: {', '.join(missing_modules)}")
        logger.error("请运行以下命令安装依赖:")
        logger.error("pip install -r requirements.txt")
        logger.error("pip install -r requirements_ui.txt")
        return False
    
    return True

def setup_environment():
    """设置环境变量"""
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
    
    # 设置 CUDA 相关环境变量
    if sys.platform == "darwin":  # macOS
        os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
    
    # 添加项目路径到 Python path
    sys.path.append(str(project_root))
    sys.path.append(str(project_root / "GPT_SoVITS"))
    sys.path.append(str(project_root / "tools"))

def start_gui():
    """启动 GUI 界面"""
    try:
        from PyQt6.QtWidgets import QApplication
        from ui_main import MainWindow
        
        app = QApplication(sys.argv)
        app.setApplicationName("AudioBookGenerator-v4")
        app.setApplicationVersion("1.0.0")
        
        # 设置应用程序图标（如果存在）
        icon_path = project_root / "icon.ico"
        if icon_path.exists():
            from PyQt6.QtGui import QIcon
            app.setWindowIcon(QIcon(str(icon_path)))
        
        window = MainWindow()
        window.show()
        
        logger.info("AudioBookGenerator-v4 GUI 已启动")
        return app.exec()
        
    except Exception as e:
        logger.error(f"启动 GUI 时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

def start_webui():
    """启动 Web UI 界面"""
    try:
        logger.info("启动 AudioBookGenerator-v4 Web UI...")
        
        # 设置环境变量
        os.environ["version"] = "v4"
        
        # 启动 webui
        import webui_v4
        
        return 0
        
    except Exception as e:
        logger.error(f"启动 Web UI 时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

def start_api():
    """启动 API 服务"""
    try:
        logger.info("启动 AudioBookGenerator-v4 API 服务...")
        
        # 启动 API 服务
        import api_v4
        
        return 0
        
    except Exception as e:
        logger.error(f"启动 API 服务时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="AudioBookGenerator-v4 - 基于 GPT-SoVITS v4 版本的有声书生成器"
    )
    parser.add_argument(
        '--mode', 
        choices=['gui', 'webui', 'api'],
        default='gui',
        help='启动模式: gui(桌面界面), webui(Web界面), api(API服务)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=9880,
        help='Web UI 或 API 服务端口 (默认: 9880)'
    )
    parser.add_argument(
        '--host',
        type=str,
        default='127.0.0.1',
        help='Web UI 或 API 服务地址 (默认: 127.0.0.1)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='启用调试模式'
    )
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 打印版本信息
    logger.info("=" * 50)
    logger.info("AudioBookGenerator-v4")
    logger.info("基于 GPT-SoVITS v4 版本的有声书生成器")
    logger.info("=" * 50)
    
    # 检查依赖项
    if not check_dependencies():
        return 1
    
    # 设置环境
    setup_environment()
    
    # 设置端口和主机
    if args.mode in ['webui', 'api']:
        os.environ["API_PORT"] = str(args.port)
        os.environ["API_HOST"] = args.host
    
    # 根据模式启动相应的服务
    if args.mode == 'gui':
        return start_gui()
    elif args.mode == 'webui':
        return start_webui()
    elif args.mode == 'api':
        return start_api()
    else:
        logger.error(f"未知的启动模式: {args.mode}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 