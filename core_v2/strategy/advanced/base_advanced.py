"""
V3 高级策略基类
定义所有高级策略必须实现的接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class AdvancedStrategy(ABC):
    """高级策略抽象基类"""
    
    @abstractmethod
    def generate(self, classes: list, features: Any, **kwargs) -> str:
        """
        生成高级 Payload
        
        Args:
            classes: 解析后的类信息列表
            features: 提取的特征对象
            **kwargs: 额外参数
            
        Returns:
            生成的 Payload 字符串
        """
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """
        获取策略描述信息
        
        Returns:
            策略描述字符串
        """
        pass
