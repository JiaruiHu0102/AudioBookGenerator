import os
import json
import shutil
from typing import Dict, List, Optional, Tuple
import time

class PresetManager:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.presets_dir = os.path.join(self.base_dir, "presets")
        self._ensure_presets_dir()
    
    def _ensure_presets_dir(self):
        """确保预设根目录存在"""
        if not os.path.exists(self.presets_dir):
            os.makedirs(self.presets_dir)
    
    def _get_preset_dir(self, name: str) -> str:
        """获取预设目录路径"""
        return os.path.join(self.presets_dir, name)
    
    def _get_settings_path(self, name: str) -> str:
        """获取预设设置文件路径"""
        return os.path.join(self._get_preset_dir(name), "settings.json")
    
    def _format_audio_filename(self, emotion: str, text: str, ext: str, preserve_timestamp: bool = False, old_filename: str = None) -> str:
        """
        格式化音频文件名，仅用于文件系统存储
        文件名仅作标识用，不影响实际使用的文本内容
        
        preserve_timestamp: 是否保留原始时间戳
        old_filename: 原始文件名，用于提取时间戳
        """
        # 移除非法字符，但这仅用于文件名，不影响数据保存
        safe_emotion = "".join(c for c in emotion if c.isalnum() or c in "._- ")
        
        # 为了避免文件名过长，我们只使用文本的简短摘要
        # 这不会影响在 all_audio_info 中保存的完整文本
        max_text_length = 30  # 设置更短的最大长度
        short_text = text[:max_text_length] + ("..." if len(text) > max_text_length else "")
        
        # 移除文件系统不允许的字符，仅用于文件名
        safe_text = "".join(c for c in short_text if c.isalnum() or c in "._- ")
        
        # 处理时间戳
        timestamp = None
        
        if preserve_timestamp and old_filename and "_" in old_filename:
            # 尝试从旧文件名中提取时间戳
            parts = old_filename.split("_")
            if len(parts) >= 2:
                timestamp_part = parts[1].split(".")[0]
                try:
                    timestamp = int(timestamp_part)
                except:
                    timestamp = None
        
        # 如果没有提取到有效的时间戳，生成新的
        if timestamp is None:
            timestamp = int(time.time() * 1000) % 10000  # 使用毫秒时间戳的后4位数字
            
        filename = f"{safe_emotion}_{timestamp}{ext}"
        return filename
    
    def add_preset(self, name: str, settings: dict, audio_files: List[Tuple[str, str, str]] = None) -> bool:
        """
        添加或更新预设
        audio_files: [(原始文件路径, 情绪标签, 语言文本)]
        """
        try:
            preset_dir = self._get_preset_dir(name)
            settings_path = self._get_settings_path(name)
            
            # 获取原始设置，以保留emotion_order顺序（如果存在）
            original_settings = {}
            if os.path.exists(settings_path):
                try:
                    with open(settings_path, 'r', encoding='utf-8') as f:
                        original_settings = json.load(f)
                except:
                    pass
            
            # 🔧 只获取音频文件的时间戳信息，避免包含模型文件
            existing_audio_info = {}
            if os.path.exists(preset_dir):
                for file in os.listdir(preset_dir):
                    # 只处理音频文件，不包括模型文件(.pth, .ckpt)和设置文件
                    if (file != "settings.json" and 
                        not file.endswith('.pth') and 
                        not file.endswith('.ckpt') and
                        (file.endswith('.wav') or file.endswith('.mp3') or file.endswith('.flac'))):
                        existing_audio_info[file] = os.path.join(preset_dir, file)
            
            # 创建预设目录
            os.makedirs(preset_dir, exist_ok=True)
            
            # 处理音频文件
            if audio_files:
                # 🔧 只获取音频文件列表，避免误删模型文件
                existing_audio_files = []
                if os.path.exists(preset_dir):
                    for file in os.listdir(preset_dir):
                        # 只处理音频文件，不包括模型文件(.pth, .ckpt)和设置文件
                        if (file != "settings.json" and 
                            not file.endswith('.pth') and 
                            not file.endswith('.ckpt') and
                            (file.endswith('.wav') or file.endswith('.mp3') or file.endswith('.flac'))):
                            existing_audio_files.append(os.path.join(preset_dir, file))
                
                # 复制新的音频文件
                new_ref_audio = []
                audio_info_list = []  # 保存所有音频的信息
                
                for src_path, emotion, text in audio_files:
                    if not os.path.exists(src_path):
                        continue
                    
                    # 检查是否应该保留原始文件名中的时间戳
                    preserve_timestamp = False
                    old_filename = None
                    
                    # 获取源文件的文件名
                    src_filename = os.path.basename(src_path)
                    
                    # 检查情况1：文件已存在于当前预设目录中（保留其时间戳）
                    for existing_file, existing_path in existing_audio_info.items():
                        if os.path.abspath(src_path) == os.path.abspath(existing_path):
                            preserve_timestamp = True
                            old_filename = existing_file
                            break
                    
                    # 检查情况2：源文件可能来自另一个预设目录（跨预设复制时保留时间戳）
                    if not preserve_timestamp and self.presets_dir in src_path:
                        preserve_timestamp = True
                        old_filename = os.path.basename(src_path)
                    
                    ext = os.path.splitext(src_path)[1]
                    new_name = self._format_audio_filename(emotion, text, ext, preserve_timestamp, old_filename)
                    dst_path = os.path.join(preset_dir, new_name)
                    
                    # 如果目标文件已存在且源文件和目标文件不同，则先删除目标文件
                    if os.path.exists(dst_path) and os.path.abspath(src_path) != os.path.abspath(dst_path):
                        os.remove(dst_path)
                    
                    # 如果源文件和目标文件不在同一位置，则复制文件
                    if os.path.abspath(src_path) != os.path.abspath(dst_path):
                        shutil.copy2(src_path, dst_path)
                    new_ref_audio.append(dst_path)
                    
                    # 保存音频信息，使用原始文本而非格式化后的文本
                    audio_info_list.append({
                        'path': dst_path,
                        'emotion': emotion,
                        'text': text  # 保存原始文本
                    })
                
                # 🔧 只删除不再使用的旧音频文件，保护模型文件
                for old_audio_file in existing_audio_files:
                    if old_audio_file not in new_ref_audio:
                        try:
                            os.remove(old_audio_file)
                            print(f"删除旧音频文件: {old_audio_file}")
                        except Exception as e:
                            print(f"删除旧音频文件失败: {old_audio_file}, 错误: {e}")
                
                # 更新设置中的音频文件路径 - 只使用第一个音频作为主参考音频
                settings['ref_audio'] = [new_ref_audio[0]] if new_ref_audio else []
                
                # 确保 ref_text 和 ref_emotion 与第一个音频匹配
                if audio_info_list:
                    # 始终使用第一个音频的文本和情绪
                    settings['ref_text'] = audio_info_list[0]['text']
                    settings['ref_emotion'] = audio_info_list[0]['emotion']
                
                # 保存所有音频信息列表
                if len(audio_info_list) >= 1:
                    settings['all_audio_info'] = audio_info_list
                    
                    # 我们不再需要保存情绪顺序，因为每次都会从文件名读取
                    # 删除可能存在的emotion_order字段，确保不会干扰文件名时间戳排序
                    if 'emotion_order' in settings:
                        del settings['emotion_order']
            
            # 保存设置
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"添加预设失败: {e}")
            return False
    
    def get_preset(self, name: str) -> Optional[Tuple[dict, List[Tuple[str, str, str]]]]:
        """
        获取预设及其音频文件
        返回: (设置, [(音频路径, 情绪标签, 语言文本)])
        """
        try:
            preset_dir = self._get_preset_dir(name)
            settings_path = self._get_settings_path(name)
            
            if not os.path.exists(settings_path):
                return None
            
            # 读取设置
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # 获取音频文件信息
            audio_files = []
            
            # 优先使用 all_audio_info 中的信息，它包含完整的原始文本和情绪
            if 'all_audio_info' in settings:
                for audio_info in settings['all_audio_info']:
                    path = audio_info['path']
                    emotion = audio_info['emotion']
                    text = audio_info['text']
                    
                    # 确认文件是否存在
                    if os.path.exists(path):
                        audio_files.append((path, emotion, text))
                    else:
                        # 如果路径不存在，尝试在预设目录中找到匹配的文件
                        found = False
                        
                        # 尝试优先查找相同情绪前缀的文件
                        for file in os.listdir(preset_dir):
                            if (file.endswith('.wav') or file.endswith('.mp3')) and file.startswith(f"{emotion}_"):
                                file_path = os.path.join(preset_dir, file)
                                # 更新路径但保留原始情绪和文本
                                audio_files.append((file_path, emotion, text))
                                # 更新 all_audio_info 中的路径
                                audio_info['path'] = file_path
                                found = True
                                break
                        
                        # 如果没有找到匹配情绪的文件，才使用目录中的第一个音频文件
                        if not found:
                            # 记录所有可用音频文件，以便警告输出
                            available_files = []
                            for file in os.listdir(preset_dir):
                                if file.endswith('.wav') or file.endswith('.mp3'):
                                    available_files.append(file)
                                    
                            if available_files:
                                # 使用第一个可用文件
                                file_path = os.path.join(preset_dir, available_files[0])
                                audio_files.append((file_path, emotion, text))
                                # 更新 all_audio_info 中的路径
                                audio_info['path'] = file_path
                                found = True
            else:
                # 如果没有 all_audio_info，则从目录中扫描音频文件并创建音频信息
                audio_info_list = []
                
                for file in os.listdir(preset_dir):
                    if file == "settings.json":
                        continue
                        
                    if file.endswith('.wav') or file.endswith('.mp3'):
                        path = os.path.join(preset_dir, file)
                        
                        # 尝试从文件名解析情绪
                        emotion = "默认"
                        if "_" in file:
                            emotion_part = file.split("_")[0]
                            emotion = emotion_part if emotion_part else "默认"
                            
                        # 使用空字符串作为文本占位符
                        text = ""
                        
                        audio_files.append((path, emotion, text))
                        audio_info_list.append({
                            'path': path,
                            'emotion': emotion,
                            'text': text
                        })
                
                # 保存新创建的 all_audio_info
                if audio_info_list:
                    settings['all_audio_info'] = audio_info_list
                    # 同时保存回文件
                    with open(settings_path, 'w', encoding='utf-8') as f:
                        json.dump(settings, f, ensure_ascii=False, indent=2)
            
            # 如果设置中没有 ref_text 和 ref_emotion，但有音频文件，则使用第一个音频文件的信息
            if audio_files and ('ref_text' not in settings or 'ref_emotion' not in settings):
                if 'ref_text' not in settings:
                    settings['ref_text'] = audio_files[0][2]
                if 'ref_emotion' not in settings:
                    settings['ref_emotion'] = audio_files[0][1]
            
            # 确保 ref_audio 也设置正确
            if audio_files and 'ref_audio' not in settings:
                settings['ref_audio'] = [audio_files[0][0]]
            
            # 确保设置中的 ref_audio 文件存在，如果不存在则更新为第一个可用的音频文件
            if 'ref_audio' in settings and settings['ref_audio'] and not os.path.exists(settings['ref_audio'][0]) and audio_files:
                settings['ref_audio'] = [audio_files[0][0]]
            
            # 确保gpt_sovits.py所需的必要字段存在
            if 'gpt_path' not in settings and 'model_path' in settings:
                settings['gpt_path'] = settings['model_path']
            
            # 确保ref_audio是字符串而不是列表（兼容gpt_sovits.py）
            if 'ref_audio' in settings and isinstance(settings['ref_audio'], list) and settings['ref_audio']:
                settings['ref_audio'] = settings['ref_audio'][0]
            elif not settings.get('ref_audio') and audio_files:
                settings['ref_audio'] = audio_files[0][0]
            
            # 确保ref_language字段存在
            if 'ref_language' not in settings:
                settings['ref_language'] = settings.get('text_lang', 'all_zh')
            
            return settings, audio_files
        except Exception as e:
            print(f"获取预设失败: {e}")
            return None
    
    def delete_preset(self, name: str) -> bool:
        """删除预设"""
        try:
            preset_dir = self._get_preset_dir(name)
            if os.path.exists(preset_dir):
                shutil.rmtree(preset_dir)
            return True
        except Exception as e:
            print(f"删除预设失败: {e}")
            return False
    
    def get_all_presets(self) -> List[Tuple[str, dict, List[Tuple[str, str, str]]]]:
        """
        获取所有预设
        返回: [(预设名, 设置, [(音频路径, 情绪标签, 语言文本)])]
        """
        try:
            result = []
            for name in os.listdir(self.presets_dir):
                preset_info = self.get_preset(name)
                if preset_info:
                    settings, audio_files = preset_info
                    result.append((name, settings, audio_files))
            return result
        except Exception as e:
            print(f"获取所有预设失败: {e}")
            return []
    
    def search_presets(self, keyword: str) -> List[Tuple[str, dict, List[Tuple[str, str, str]]]]:
        """
        搜索预设
        返回: [(预设名, 设置, [(音频路径, 情绪标签, 语言文本)])]
        """
        try:
            result = []
            for name in os.listdir(self.presets_dir):
                if keyword.lower() in name.lower():
                    preset_info = self.get_preset(name)
                    if preset_info:
                        settings, audio_files = preset_info
                        # 也搜索情绪标签和语言文本
                        if any(keyword.lower() in f"{emotion}{text}".lower() 
                              for _, emotion, text in audio_files):
                            result.append((name, settings, audio_files))
            return result
        except Exception as e:
            print(f"搜索预设失败: {e}")
            return []
    
    def get_preset_emotions(self, preset_name: str) -> List[str]:
        """获取预设的情绪列表，根据音频文件名中的时间戳升序排列（小数字排在前面）"""
        try:
            preset_info = self.get_preset(preset_name)
            if not preset_info:
                return []
            
            settings, audio_files = preset_info
            
            # 每次都从文件名提取时间戳信息
            emotion_timestamps = {}
            all_emotions = []  # 用于记录情绪出现的顺序
            
            # 首先收集所有的音频文件信息
            files_info = []
            for file_path, emotion, _ in audio_files:
                if emotion not in all_emotions:
                    all_emotions.append(emotion)
                
                file_name = os.path.basename(file_path)
                timestamp = 0
                
                # 尝试从文件名中提取时间戳部分
                if "_" in file_name:
                    parts = file_name.split("_")
                    if len(parts) >= 2:
                        timestamp_part = parts[1].split(".")[0]
                        try:
                            timestamp = int(timestamp_part)
                        except:
                            timestamp = int(os.path.getmtime(file_path))
                else:
                    timestamp = int(os.path.getmtime(file_path))
                
                files_info.append((emotion, timestamp, file_name))
            
            # 按情绪分组，每个情绪只保留具有最新/最大时间戳的记录
            for emotion, timestamp, file_name in files_info:
                if emotion not in emotion_timestamps or timestamp > emotion_timestamps[emotion]:
                    emotion_timestamps[emotion] = timestamp
            
            # 按时间戳升序排序情绪（小的数字排在前面）
            sorted_emotions = sorted(emotion_timestamps.items(), key=lambda x: x[1], reverse=False)
            emotions_list = [emotion for emotion, _ in sorted_emotions]
            
            # 如果有情绪没有时间戳（极少数情况），添加到列表末尾
            for emotion in all_emotions:
                if emotion not in emotions_list:
                    emotions_list.append(emotion)
            
            return emotions_list
        except Exception as e:
            print(f"获取预设情绪列表失败: {e}")
            return []