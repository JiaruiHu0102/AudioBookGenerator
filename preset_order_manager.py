import os
import json
from typing import Dict, List, Set
from pypinyin import lazy_pinyin


class PresetOrderManager:
    """预设排序管理器 - 管理男主/女主设置和拼音排序"""
    
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.base_dir, "preset_order_config.json")
        self.male_leads: Set[str] = set()  # 男主预设集合
        self.female_leads: Set[str] = set()  # 女主预设集合
        self.load_config()
    
    def load_config(self):
        """从配置文件加载男主/女主设置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.male_leads = set(config.get('male_leads', []))
                    self.female_leads = set(config.get('female_leads', []))
        except Exception as e:
            print(f"加载预设排序配置失败: {e}")
    
    def save_config(self):
        """保存男主/女主设置到配置文件"""
        try:
            config = {
                'male_leads': list(self.male_leads),
                'female_leads': list(self.female_leads)
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存预设排序配置失败: {e}")
    
    def set_male_lead(self, preset_name: str):
        """设置预设为男主"""
        # 从女主中移除（如果存在）
        self.female_leads.discard(preset_name)
        # 添加到男主
        self.male_leads.add(preset_name)
        self.save_config()
    
    def set_female_lead(self, preset_name: str):
        """设置预设为女主"""
        # 从男主中移除（如果存在）
        self.male_leads.discard(preset_name)
        # 添加到女主
        self.female_leads.add(preset_name)
        self.save_config()
    
    def remove_lead_status(self, preset_name: str):
        """移除预设的男主/女主状态"""
        self.male_leads.discard(preset_name)
        self.female_leads.discard(preset_name)
        self.save_config()
    
    def is_male_lead(self, preset_name: str) -> bool:
        """检查是否为男主"""
        return preset_name in self.male_leads
    
    def is_female_lead(self, preset_name: str) -> bool:
        """检查是否为女主"""
        return preset_name in self.female_leads
    
    def get_pinyin_sort_key(self, text: str) -> str:
        """获取拼音排序键"""
        return ''.join(lazy_pinyin(text)).lower()
    
    def sort_presets(self, preset_names: List[str]) -> List[str]:
        """
        对预设列表进行排序
        排序规则：男主在前，女主在后，其他按拼音排序
        """
        try:
            male_presets = []
            female_presets = []
            other_presets = []
            
            # 分类预设
            for name in preset_names:
                if self.is_male_lead(name):
                    male_presets.append(name)
                elif self.is_female_lead(name):
                    female_presets.append(name)
                else:
                    other_presets.append(name)
            
            # 分别按拼音排序
            male_presets.sort(key=self.get_pinyin_sort_key)
            female_presets.sort(key=self.get_pinyin_sort_key)
            other_presets.sort(key=self.get_pinyin_sort_key)
            
            # 组合：男主 + 其他 + 女主
            result = male_presets + other_presets + female_presets
            return result
        except Exception as e:
            print(f"预设排序失败: {e}")
            # 失败时返回原始列表
            return preset_names
    
    def cleanup_deleted_presets(self, existing_presets: List[str]):
        """清理已删除的预设配置"""
        # 移除不再存在的预设
        existing_set = set(existing_presets)
        self.male_leads &= existing_set
        self.female_leads &= existing_set
        self.save_config() 