from abc import ABC, abstractmethod
from ..model.class_info import ClassInfo, FeatureSet

class PayloadStrategy(ABC):
    """Payload 生成策略基类"""
    @abstractmethod
    def generate(self, class_info: ClassInfo, features: FeatureSet, tags: list) -> str:
        pass
