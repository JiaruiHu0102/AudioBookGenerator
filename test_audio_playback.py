#!/usr/bin/env python3
"""
音频播放功能测试脚本
用于验证QMediaPlayer在macOS上的重复播放问题是否修复
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt6.QtCore import QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

class AudioTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("音频播放测试")
        self.setGeometry(100, 100, 300, 150)
        
        # 初始化播放器
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        
        # 设置测试音频文件路径
        self.audio_path = "preview_audio/preview.wav"  # 请确保此文件存在
        if not os.path.exists(self.audio_path):
            # 尝试其他可能的路径
            working_dir = "Working"
            if os.path.exists(working_dir):
                for root, dirs, files in os.walk(working_dir):
                    for file in files:
                        if file.endswith('.wav'):
                            self.audio_path = os.path.join(root, file)
                            break
                    if self.audio_path != "preview_audio/preview.wav":
                        break
        
        self.init_ui()
        
    def init_ui(self):
        widget = QWidget()
        self.setCentralWidget(widget)
        layout = QVBoxLayout(widget)
        
        # 状态标签
        self.status_label = QLabel(f"音频文件: {self.audio_path}")
        layout.addWidget(self.status_label)
        
        # 播放按钮（原始方法）
        self.play_btn1 = QPushButton("播放 (原始方法)")
        self.play_btn1.clicked.connect(self.play_original)
        layout.addWidget(self.play_btn1)
        
        # 播放按钮（修复方法）
        self.play_btn2 = QPushButton("播放 (修复方法)")
        self.play_btn2.clicked.connect(self.play_fixed)
        layout.addWidget(self.play_btn2)
        
        # 测试计数器
        self.test_count = 0
        self.test_label = QLabel("测试次数: 0")
        layout.addWidget(self.test_label)
        
    def play_original(self):
        """原始播放方法（可能有问题）"""
        try:
            if not os.path.exists(self.audio_path):
                self.status_label.setText("音频文件不存在")
                return
                
            self.player.stop()
            self.player.setSource(QUrl.fromLocalFile(self.audio_path))
            self.player.play()
            
            self.test_count += 1
            self.test_label.setText(f"原始方法测试次数: {self.test_count}")
            self.status_label.setText("使用原始方法播放...")
        except Exception as e:
            self.status_label.setText(f"原始方法出错: {str(e)}")
    
    def play_fixed(self):
        """修复后的播放方法"""
        try:
            if not os.path.exists(self.audio_path):
                self.status_label.setText("音频文件不存在")
                return
            
            # 重新创建播放器实例
            self.player.stop()
            self.player.setSource(QUrl())  # 清空音频源
            
            del self.player
            del self.audio_output
            
            self.player = QMediaPlayer()
            self.audio_output = QAudioOutput()
            self.player.setAudioOutput(self.audio_output)
            
            self.player.setSource(QUrl.fromLocalFile(self.audio_path))
            self.player.play()
            
            self.test_count += 1
            self.test_label.setText(f"修复方法测试次数: {self.test_count}")
            self.status_label.setText("使用修复方法播放...")
        except Exception as e:
            self.status_label.setText(f"修复方法出错: {str(e)}")

def main():
    app = QApplication(sys.argv)
    window = AudioTestWindow()
    window.show()
    
    print("=== 音频播放测试说明 ===")
    print("1. 点击'播放 (原始方法)'按钮测试原始播放方式")
    print("2. 点击'播放 (修复方法)'按钮测试修复后的播放方式")
    print("3. 多次点击同一个按钮，观察是否每次都能播放声音")
    print("4. 如果修复方法每次都能播放，说明问题已解决")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 