import os
import re
from typing import List, Dict
from .php_parser import PhpParserV2
from ..model.class_info import ClassInfo

class MultiFileAnalyzer:
    """多文件分析与符号表合并"""

    def __init__(self):
        self.parser = PhpParserV2()
        self.file_map = {} # path -> content
        self.class_map = {} # class_name -> ClassInfo

    def analyze_directory(self, root_path: str, progress_callback=None) -> List[ClassInfo]:
        """递归分析目录下的所有 PHP 文件"""
        php_files = []
        for dirpath, _, filenames in os.walk(root_path):
            for f in filenames:
                if f.endswith('.php'):
                    php_files.append(os.path.join(dirpath, f))
        
        if len(php_files) > 50 and progress_callback:
            progress_callback(f"警告: 检测到 {len(php_files)} 个文件，解析可能较慢")

        all_classes = []
        total = len(php_files)
        for i, path in enumerate(php_files):
            if progress_callback:
                progress_callback(f"正在解析 {i+1}/{total}: {os.path.basename(path)}")
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                classes = self.parser.parse(content)
                for cls in classes:
                    cls.source_file = path
                    self.class_map[cls.name] = cls
                all_classes.extend(classes)
            except Exception as e:
                print(f"Error parsing {path}: {e}")

        # 第二遍：处理继承与包含关系
        self._resolve_inheritance(all_classes)
        return list(self.class_map.values())

    def _resolve_inheritance(self, classes: List[ClassInfo]):
        """合并父类属性与方法到子类"""
        for cls in classes:
            if cls.parent_class and cls.parent_class in self.class_map:
                parent = self.class_map[cls.parent_class]
                # 简单合并：如果子类没有该属性/方法，则从父类继承
                for name, prop in parent.properties.items():
                    if name not in cls.properties:
                        cls.properties[name] = prop
                for name, method in parent.methods.items():
                    if name not in cls.methods:
                        cls.methods[name] = method
