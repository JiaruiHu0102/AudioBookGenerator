import os
import sys
import time
import logging
import torch
from typing import Dict, Optional, Tuple
from pathlib import Path

# 设置环境变量
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from GPT_SoVITS.TTS_infer_pack.TTS import TTS, TTS_Config
except ImportError as e:
    logging.error(f"无法导入TTS模块: {e}")
    TTS = None
    TTS_Config = None

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class ModelCache:
    """模型缓存管理器 - 实现懒加载缓存策略"""
    
    def __init__(self, max_models: int = 3):
        """
        初始化模型缓存
        
        Args:
            max_models: 最大缓存模型数量（对于16GB内存推荐2-3个）
        """
        self.max_models = max_models
        self.cache: Dict[str, Dict] = {}  # 缓存字典: {cache_key: {tts, config, last_used}}
        self.device = "cpu"  # 默认使用CPU
        
        # 统计信息
        self.cache_hits = 0
        self.cache_misses = 0
        
    def _generate_cache_key(self, gpt_path: str, sovits_path: str) -> str:
        """生成缓存键"""
        # 使用文件路径的组合作为唯一标识
        return f"{os.path.basename(gpt_path)}#{os.path.basename(sovits_path)}"
    
    def set_device(self, device: str = "auto"):
        """设置计算设备"""
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        logger.info(f"模型缓存设备设置为: {self.device}")
    
    def _create_tts_config(self, gpt_path: str, sovits_path: str) -> Optional['TTS_Config']:
        """创建TTS配置"""
        if TTS_Config is None:
            logger.error("TTS_Config类未能成功导入")
            return None
            
        try:
            config_dict = {
                "device": self.device,
                "is_half": True,  # 使用半精度节省显存
                "version": "v4",  # 使用v4版本
                "t2s_weights_path": gpt_path,
                "vits_weights_path": sovits_path,
                "cnhuhbert_base_path": "GPT_SoVITS/pretrained_models/chinese-hubert-base",
                "bert_base_path": "GPT_SoVITS/pretrained_models/chinese-roberta-wwm-ext-large",
            }
            return TTS_Config(config_dict)
        except Exception as e:
            logger.error(f"创建TTS配置失败: {e}")
            return None
    
    def _load_model(self, gpt_path: str, sovits_path: str) -> Optional['TTS']:
        """加载模型到内存"""
        if TTS is None:
            logger.error("TTS类未能成功导入")
            return None
            
        try:
            logger.info(f"正在加载新模型: GPT={os.path.basename(gpt_path)}, SoVITS={os.path.basename(sovits_path)}")
            start_time = time.time()
            
            # 检查模型文件是否存在
            if not os.path.exists(gpt_path) or not os.path.exists(sovits_path):
                logger.error(f"模型文件不存在: GPT={gpt_path}, SoVITS={sovits_path}")
                return None
            
            # 创建配置
            config = self._create_tts_config(gpt_path, sovits_path)
            if config is None:
                return None
            
            # 初始化TTS
            tts = TTS(config)
            
            load_time = time.time() - start_time
            logger.info(f"模型加载完成，耗时: {load_time:.2f}秒")
            
            return tts
            
        except Exception as e:
            logger.error(f"加载模型时发生错误: {str(e)}")
            return None
    
    def _evict_oldest(self):
        """移除最久未使用的模型"""
        if not self.cache:
            return
            
        # 找到最久未使用的模型
        oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]['last_used'])
        
        logger.info(f"缓存已满，移除最久未使用的模型: {oldest_key}")
        
        # 清理GPU/CPU内存
        try:
            del self.cache[oldest_key]['tts']
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception as e:
            logger.warning(f"清理模型内存时出错: {e}")
        
        # 从缓存中移除
        del self.cache[oldest_key]
    
    def get_model(self, gpt_path: str, sovits_path: str) -> Optional['TTS']:
        """
        获取模型（使用缓存策略）
        
        Args:
            gpt_path: GPT模型路径
            sovits_path: SoVITS模型路径
            
        Returns:
            TTS实例或None
        """
        cache_key = self._generate_cache_key(gpt_path, sovits_path)
        
        # 检查缓存是否命中
        if cache_key in self.cache:
            # 缓存命中
            self.cache_hits += 1
            self.cache[cache_key]['last_used'] = time.time()
            logger.info(f"缓存命中: {cache_key}")
            return self.cache[cache_key]['tts']
        
        # 缓存未命中，需要加载模型
        self.cache_misses += 1
        logger.info(f"缓存未命中: {cache_key}")
        
        # 如果缓存已满，移除最久未使用的模型
        if len(self.cache) >= self.max_models:
            self._evict_oldest()
        
        # 加载新模型
        tts = self._load_model(gpt_path, sovits_path)
        if tts is None:
            return None
        
        # 将模型添加到缓存
        self.cache[cache_key] = {
            'tts': tts,
            'gpt_path': gpt_path,
            'sovits_path': sovits_path,
            'last_used': time.time()
        }
        
        logger.info(f"模型已缓存: {cache_key}")
        return tts
    
    def clear_cache(self):
        """清空所有缓存"""
        logger.info("清空模型缓存")
        for cache_key in list(self.cache.keys()):
            try:
                del self.cache[cache_key]['tts']
            except:
                pass
        
        self.cache.clear()
        
        # 清理GPU内存
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    def get_cache_info(self) -> Dict:
        """获取缓存统计信息"""
        cache_info = {
            'cached_models': len(self.cache),
            'max_models': self.max_models,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'hit_rate': self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0,
            'cached_model_list': []
        }
        
        for cache_key, info in self.cache.items():
            cache_info['cached_model_list'].append({
                'key': cache_key,
                'gpt_model': os.path.basename(info['gpt_path']),
                'sovits_model': os.path.basename(info['sovits_path']),
                'last_used': time.strftime('%H:%M:%S', time.localtime(info['last_used']))
            })
        
        return cache_info
    
    def preload_models(self, model_pairs: list):
        """
        预加载指定的模型对
        
        Args:
            model_pairs: [(gpt_path, sovits_path), ...] 模型路径对列表
        """
        logger.info("开始预加载模型...")
        
        for gpt_path, sovits_path in model_pairs:
            if len(self.cache) >= self.max_models:
                logger.warning("缓存已满，停止预加载")
                break
                
            cache_key = self._generate_cache_key(gpt_path, sovits_path)
            if cache_key not in self.cache:
                self.get_model(gpt_path, sovits_path)
        
        logger.info(f"预加载完成，当前缓存模型数: {len(self.cache)}")

# 全局模型缓存实例
_global_model_cache = None

def get_global_model_cache() -> ModelCache:
    """获取全局模型缓存实例"""
    global _global_model_cache
    if _global_model_cache is None:
        _global_model_cache = ModelCache(max_models=3)  # 16GB内存推荐最多缓存3个模型
    return _global_model_cache

def set_cache_device(device: str = "auto"):
    """设置全局缓存的设备"""
    cache = get_global_model_cache()
    cache.set_device(device)

def clear_global_cache():
    """清空全局缓存"""
    cache = get_global_model_cache()
    cache.clear_cache() 