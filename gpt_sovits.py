import os
import torch
import numpy as np
from typing import List, Dict, Optional, Tuple
import logging
from pathlib import Path
import shutil
import re
import sys
import time

# 设置环境变量
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from GPT_SoVITS.TTS_infer_pack.TTS import TTS, TTS_Config
from GPT_SoVITS.AR.models.t2s_lightning_module import Text2SemanticLightningModule
from model_cache import get_global_model_cache

logging.basicConfig(level=logging.WARNING)  # 只显示警告和错误
logger = logging.getLogger(__name__)

class GPTSoVITS:
    def __init__(self):
        self.device = "cpu"  # 强制使用CPU
        self.tts = None
        self.current_preset = None
        self.preview_dir = Path("preview_audio")
        self.output_dir = Path("output_audio")
        self.preview_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        self._latest_ref_audio = None  # 添加属性追踪最新使用的参考音频路径
        
        # 获取全局模型缓存实例
        self.model_cache = get_global_model_cache()
        
        # 当前加载的模型信息（用于避免重复缓存查询）
        self._current_model_key = None
        
        # v4 版本的新配置参数（优化性能）
        self.v4_config = {
            'sample_steps': 16,  # 降低采样步数以提升速度（原32）
            'if_sr': False,      # 关闭音频超分辨率以提升速度
            'native_48k': True,  # v4 版本原生支持 48k 采样率
            'bigvgan_enabled': True,  # v4 版本使用 BigVGAN
        }
        
    def extract_book_name(self, file_path: str) -> str:
        """从文件路径中提取书名"""
        # 获取文件名（不含扩展名）
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        
        # 如果文件名包含下划线，取第一个下划线之前的部分作为书名
        if "_" in base_name:
            book_name = base_name.split("_")[0]
        else:
            book_name = base_name
            
        # 移除可能的特殊字符
        book_name = re.sub(r'[^\w\-\.]', '', book_name)
        return book_name
        
    def get_latest_ref_audio(self) -> Optional[str]:
        """获取最新使用的参考音频路径"""
        return self._latest_ref_audio
        
    def set_latest_ref_audio(self, path: str):
        """设置最新使用的参考音频路径"""
        self._latest_ref_audio = path
        
    def check_gpu_availability(self) -> bool:
        """检查GPU可用性"""
        return torch.cuda.is_available()
        
    def set_device(self, device: str = "auto"):
        """设置计算设备"""
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        logger.info(f"设备设置为: {self.device}")
        
        # 同时设置模型缓存的设备
        self.model_cache.set_device(self.device)
        
    def load_models(self, gpt_path: str, sovits_path: str) -> bool:
        """加载GPT和SoVITS模型（使用缓存）"""
        try:
            # 生成模型键
            model_key = self.model_cache._generate_cache_key(gpt_path, sovits_path)
            
            # 如果当前已经是相同的模型，直接返回成功
            if self._current_model_key == model_key and self.tts is not None:
                logger.info(f"模型已加载，跳过重复加载: {model_key}")
                return True
            
            logger.info(f"使用缓存加载模型: GPT={os.path.basename(gpt_path)}, SoVITS={os.path.basename(sovits_path)}")
            
            # 检查模型文件是否存在
            if not os.path.exists(gpt_path) or not os.path.exists(sovits_path):
                logger.error("模型文件不存在")
                return False
            
            # 确保模型缓存使用相同的设备
            self.model_cache.set_device(self.device)
            
            # 从缓存获取模型
            self.tts = self.model_cache.get_model(gpt_path, sovits_path)
            
            # 检查TTS初始化是否成功
            success = self.tts is not None
            
            if success:
                self._current_model_key = model_key
                logger.info(f"模型加载成功: {model_key}")
                
                # 输出缓存统计信息
                cache_info = self.model_cache.get_cache_info()
                logger.info(f"缓存统计 - 命中率: {cache_info['hit_rate']:.2%}, 缓存模型数: {cache_info['cached_models']}/{cache_info['max_models']}")
                
                return True
            else:
                logger.error("模型加载失败")
                return False
                
        except Exception as e:
            logger.error(f"加载模型时发生错误: {str(e)}")
            return False

# 在 gpt_sovits.py 文件中

    def set_preset(self, preset: Dict) -> bool:
        """设置预设配置"""
        try:
            # 关键修复：确保 self.current_preset 包含所有信息，包括 all_audio_info
            self.current_preset = preset.copy()
            
            # 确保预设包含必要的字段
            required_fields = ['gpt_path', 'sovits_path', 'ref_audio', 'ref_text', 'ref_language']
            for field in required_fields:
                if field not in preset:
                    logger.error(f"预设缺少必要字段: {field}")
                    return False
            
            # 检查参考音频文件是否存在
            ref_audio_path = preset['ref_audio']
            if not os.path.exists(ref_audio_path):
                logger.error(f"参考音频文件不存在: {ref_audio_path}")
                return False
                
            # 设置最新参考音频
            self.set_latest_ref_audio(ref_audio_path)
            
            # 检查模型文件是否存在
            gpt_path = preset['gpt_path']
            sovits_path = preset['sovits_path']
            
            if not os.path.exists(gpt_path) or not os.path.exists(sovits_path):
                logger.error("模型文件不存在")
                return False
            
            # 使用缓存加载模型（这里会自动检查是否需要重新加载）
            if not self.load_models(gpt_path, sovits_path):
                return False
                
            # 更新v4版本的配置参数
            v4_config_updates = {}
            if 'sample_steps' in preset:
                v4_config_updates['sample_steps'] = preset['sample_steps']
            if 'if_sr' in preset:
                v4_config_updates['if_sr'] = preset['if_sr']
            if 'aux_ref_enabled' in preset:
                v4_config_updates['aux_ref_enabled'] = preset['aux_ref_enabled']
            
            if v4_config_updates:
                self.update_v4_config(v4_config_updates)
            
            logger.info("预设设置成功")
            return True
                
        except Exception as e:
            logger.error(f"设置预设时发生错误: {str(e)}")
            return False

    def _prepare_tts_inputs(self, text: str, speed_factor: float = None, emotion: str = None) -> dict:
        """准备TTS输入参数 - 适配v4版本 (已修复)"""
        if not self.current_preset:
            logger.error("未设置预设")
            return None
            
        # 初始时，使用预设中的默认参考音频和文本
        ref_audio = self.current_preset['ref_audio']
        ref_text = self.current_preset['ref_text']
        ref_language = self.current_preset['ref_language']
        
        # --- 关键修复：直接使用 self.current_preset 中已有的 all_audio_info 列表来查找情绪 ---
        if emotion and 'all_audio_info' in self.current_preset:
            all_audio_info = self.current_preset['all_audio_info']
            found = False
            for audio_info in all_audio_info:
                if audio_info.get('emotion') == emotion:
                    ref_audio = audio_info.get('path', ref_audio)
                    ref_text = audio_info.get('text', ref_text)
                    found = True
                    break # 找到匹配项后立即中断循环
            if not found:
                logger.warning(f"在预设中未找到情绪 '{emotion}' 对应的参考音频，将使用默认参考。")
        # --- 修复结束 ---
                    
        logger.info(f"实际使用的参考音频: {ref_audio}")
        logger.info(f"实际使用的参考文本: {ref_text}")
        
        # 构建输入参数
        inputs = {
            'refer_wav_path': ref_audio,
            'prompt_text': ref_text,
            'prompt_language': ref_language,
            'text': text,
            'text_language': self.current_preset.get('text_language', 'zh'),
            'cut_punc': self.current_preset.get('cut_punc', ''),
            'top_k': self.current_preset.get('top_k', 15),
            'top_p': self.current_preset.get('top_p', 1.0),
            'temperature': self.current_preset.get('temperature', 1.0),
            'speed': speed_factor if speed_factor is not None else self.current_preset.get('speed_factor', 1.0),
            
            'sample_steps': self.v4_config['sample_steps'],
            'if_sr': self.v4_config['if_sr'],
            'aux_ref_audio_paths': self.current_preset.get('aux_ref_audio_paths', []),
            
            'fragment_interval': self.current_preset.get('fragment_interval', 0.3),
            'repetition_penalty': self.current_preset.get('repetition_penalty', 1.35),
        }
        
        logger.warning(f"🔥 TTS参数调试 - sample_steps: {inputs['sample_steps']}, if_sr: {inputs['if_sr']}")
        
        return inputs

    def generate_preview(self, text: str, emotion: str = None) -> Optional[str]:
        """生成预览音频 - 适配v4版本"""
        if not self.tts or not self.current_preset:
            logger.error("TTS未初始化或未设置预设")
            return None
            
        try:
            # 准备输入参数
            inputs = self._prepare_tts_inputs(text, emotion=emotion)
            if not inputs:
                return None
                
            # 生成输出文件路径
            output_path = self.preview_dir / "preview.wav"
            
            # 获取用户设置的文本切分方法，默认为cut1（每4句切分）以平衡质量和速度
            text_split_method = self.current_preset.get('text_split_method', 'cut1')
            logger.info(f"使用文本切分方法: {text_split_method}")
            
            # 使用TTS.run方法而不是generate
            tts_inputs = {
                'text': inputs['text'],
                'text_lang': inputs['text_language'],
                'ref_audio_path': inputs['refer_wav_path'],
                'aux_ref_audio_paths': inputs['aux_ref_audio_paths'],
                'prompt_text': inputs['prompt_text'],
                'prompt_lang': inputs['prompt_language'],
                'top_k': inputs['top_k'],
                'top_p': inputs['top_p'],
                'temperature': inputs['temperature'],
                'speed_factor': inputs['speed'],
                'sample_steps': inputs['sample_steps'],
                'super_sampling': inputs['if_sr'],
                'text_split_method': text_split_method,
                'batch_size': 1,
                'return_fragment': False,
                'fragment_interval': inputs.get('fragment_interval', 0.3),
                'seed': -1,
                'parallel_infer': self.current_preset.get('parallel_infer', False),
                'repetition_penalty': inputs.get('repetition_penalty', 1.35),
            }
            
            # 🚨 添加TTS调用前的参数确认
            logger.warning(f"🔥 TTS调用参数确认 - sample_steps: {tts_inputs['sample_steps']}, super_sampling: {tts_inputs['super_sampling']}, text_split_method: {tts_inputs['text_split_method']}")
            
            # 调用TTS生成
            for sample_rate, audio_data in self.tts.run(tts_inputs):
                # 保存音频文件
                import soundfile as sf
                sf.write(str(output_path), audio_data, samplerate=sample_rate)
                logger.info(f"预览音频生成成功: {output_path}")
                return str(output_path)
            
            logger.error("音频生成失败")
            return None
                
        except Exception as e:
            logger.error(f"生成预览音频时发生错误: {str(e)}")
            return None

    def generate_audio(self, text: str, output_path: str, emotion: str = None) -> bool:
        """生成音频文件 - 适配v4版本"""
        if not self.tts or not self.current_preset:
            logger.error("TTS未初始化或未设置预设")
            return False
            
        try:
            # 准备输入参数
            inputs = self._prepare_tts_inputs(text, emotion=emotion)
            if not inputs:
                return False
                
            # 获取用户设置的文本切分方法，默认为cut1（每4句切分）以平衡质量和速度
            text_split_method = self.current_preset.get('text_split_method', 'cut1')
            logger.info(f"使用文本切分方法: {text_split_method}")
                
            # 使用TTS.run方法而不是generate
            tts_inputs = {
                'text': inputs['text'],
                'text_lang': inputs['text_language'],
                'ref_audio_path': inputs['refer_wav_path'],
                'aux_ref_audio_paths': inputs['aux_ref_audio_paths'],
                'prompt_text': inputs['prompt_text'],
                'prompt_lang': inputs['prompt_language'],
                'top_k': inputs['top_k'],
                'top_p': inputs['top_p'],
                'temperature': inputs['temperature'],
                'speed_factor': inputs['speed'],
                'sample_steps': inputs['sample_steps'],
                'super_sampling': inputs['if_sr'],
                'text_split_method': text_split_method,
                'batch_size': self.current_preset.get('batch_size', 1),
                'return_fragment': False,
                'fragment_interval': inputs.get('fragment_interval', 0.3),
                'seed': -1,
                'parallel_infer': self.current_preset.get('parallel_infer', False),
                'repetition_penalty': inputs.get('repetition_penalty', 1.35),
            }
            
            # 🚨 添加TTS调用前的参数确认（generate_audio方法）
            logger.warning(f"🔥 generate_audio TTS调用参数 - sample_steps: {tts_inputs['sample_steps']}, super_sampling: {tts_inputs['super_sampling']}, text_split_method: {tts_inputs['text_split_method']}")
            
            # 调用TTS生成
            for sample_rate, audio_data in self.tts.run(tts_inputs):
                # 保存音频文件
                import soundfile as sf
                sf.write(output_path, audio_data, samplerate=sample_rate)
                logger.info(f"音频生成成功: {output_path}")
                return True
            
            logger.error("音频生成失败")
            return False
                
        except Exception as e:
            logger.error(f"生成音频时发生错误: {str(e)}")
            return False

    def generate_book_audio(self, segments: List[str], txt_file_path: str) -> bool:
        """生成完整的有声书音频 - 适配v4版本"""
        if not segments:
            logger.error("没有文本段落")
            return False
            
        try:
            # 提取书名
            book_name = self.extract_book_name(txt_file_path)
            
            # 创建输出目录
            book_output_dir = self.output_dir / book_name
            book_output_dir.mkdir(exist_ok=True)
            
            # 生成各段音频
            audio_files = []
            for i, segment in enumerate(segments):
                if not segment.strip():
                    continue
                    
                segment_file = book_output_dir / f"segment_{i+1:03d}.wav"
                if self.generate_audio(segment, str(segment_file)):
                    audio_files.append(str(segment_file))
                else:
                    logger.error(f"段落 {i+1} 生成失败")
                    return False
            
            # 合并音频文件
            final_output = book_output_dir / f"{book_name}_完整版.wav"
            if self._merge_audio_files(audio_files, str(final_output)):
                logger.info(f"有声书生成成功: {final_output}")
                return True
            else:
                logger.error("音频合并失败")
                return False
                
        except Exception as e:
            logger.error(f"生成有声书时发生错误: {str(e)}")
            return False
            
    def _merge_audio_files(self, audio_files: List[str], output_path: str) -> bool:
        """合并音频文件"""
        try:
            import soundfile as sf
            
            # 读取所有音频文件
            audio_data = []
            for file_path in audio_files:
                data, samplerate = sf.read(file_path)
                audio_data.append(data)
            
            # 合并音频数据
            if audio_data:
                merged_audio = np.concatenate(audio_data)
                sf.write(output_path, merged_audio, samplerate=48000)  # v4 版本使用 48k
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"合并音频时发生错误: {str(e)}")
            return False

    def get_device_info(self) -> Dict:
        """获取设备信息"""
        return {
            'current_device': self.device,
            'cuda_available': torch.cuda.is_available(),
            'cuda_device_count': torch.cuda.device_count() if torch.cuda.is_available() else 0,
            'v4_features': self.v4_config,
        }
        
    def update_v4_config(self, config: Dict):
        """更新v4版本的配置参数"""
        self.v4_config.update(config)
        logger.info(f"v4 配置已更新: {self.v4_config}")
        
    def get_supported_languages(self) -> List[str]:
        """获取支持的语言列表"""
        return ['zh', 'en', 'ja', 'ko', 'yue']
        
    def get_supported_emotions(self) -> List[str]:
        """获取当前预设支持的情感列表"""
        if self.current_preset and 'emotions' in self.current_preset:
            return list(self.current_preset['emotions'].keys())
        return []
    
    def get_cache_info(self) -> Dict:
        """获取模型缓存信息"""
        return self.model_cache.get_cache_info()
    
    def clear_model_cache(self):
        """清空模型缓存"""
        logger.info("清空模型缓存")
        self.model_cache.clear_cache()
        self.tts = None
        self._current_model_key = None
    
    def preload_preset_models(self, presets: List[Dict]):
        """预加载指定预设的模型"""
        model_pairs = []
        for preset in presets:
            if 'gpt_path' in preset and 'sovits_path' in preset:
                model_pairs.append((preset['gpt_path'], preset['sovits_path']))
        
        if model_pairs:
            logger.info(f"开始预加载 {len(model_pairs)} 个预设的模型")
            self.model_cache.preload_models(model_pairs)