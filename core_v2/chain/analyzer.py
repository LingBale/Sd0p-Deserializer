import re
from typing import List, Dict, Any
from ..model.class_info import ClassInfo

class CallGraphBuilder:
    """构建 POP 链调用图"""
    
    def __init__(self):
        self.nodes = []
        self.edges = []

    def build(self, classes: List[ClassInfo]) -> Dict[str, Any]:
        """
        分析类之间的调用关系
        :param classes: 解析出的所有类信息
        :return: 包含 nodes 和 edges 的字典
        """
        class_map = {c.name: c for c in classes}
        self.nodes = [{"id": c.name, "label": c.name, "type": "class"} for c in classes]
        self.edges = []

        for cls in classes:
            self._analyze_methods(cls, class_map)
        
        return {"nodes": self.nodes, "edges": self.edges}

    def _analyze_methods(self, cls: ClassInfo, class_map: Dict[str, ClassInfo]):
        """分析方法体中的 new 表达式和属性传递"""
        for method_name, method in cls.methods.items():
            # 匹配 new ClassName($this->prop) 模式
            pattern = r'new\s+(\w+)\s*\(\s*\$this->(\w+)'
            for match in re.finditer(pattern, method.body):
                target_class = match.group(1)
                source_prop = match.group(2)
                
                if target_class in class_map:
                    self.edges.append({
                        "from": cls.name,
                        "to": target_class,
                        "label": f"{method_name}()\nvia ${source_prop}"
                    })
