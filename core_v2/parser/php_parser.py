import re
from typing import List, Dict, Optional
from ..model.class_info import ClassInfo, PropertyInfo, MethodInfo

class PhpParserV2:
    def __init__(self):
        self.classes: List[ClassInfo] = []
        self.class_map: Dict[str, ClassInfo] = {}
        self.code = ""

    def parse(self, code: str) -> List[ClassInfo]:
        self.code = code
        self.classes = []
        self.class_map = {}
        self._extract_classes()
        self._merge_inheritance()
        return self.classes

    def _find_matching_brace(self, start: int) -> int:
        """状态机：查找匹配的右大括号"""
        i = start
        length = len(self.code)
        brace_count = 1
        in_string = False
        string_char = None
        in_single_comment = False
        in_multi_comment = False
        escaped = False
        
        while i < length and brace_count > 0:
            ch = self.code[i]
            next_ch = self.code[i + 1] if i + 1 < length else ''
            
            if escaped:
                escaped = False
                i += 1
                continue
            if ch == '\\' and in_string:
                escaped = True
                i += 1
                continue
            
            if not in_string and not in_multi_comment and ch == '/' and next_ch == '/':
                in_single_comment = True
                i += 2
                continue
            if not in_string and not in_multi_comment and ch == '/' and next_ch == '*':
                in_multi_comment = True
                i += 2
                continue
            
            if in_single_comment:
                if ch == '\n': in_single_comment = False
                i += 1
                continue
            if in_multi_comment:
                if ch == '*' and next_ch == '/':
                    in_multi_comment = False
                    i += 2
                    continue
                i += 1
                continue
            
            if not in_string and ch in ('"', "'"):
                in_string = True
                string_char = ch
                i += 1
                continue
            if in_string:
                if ch == string_char: in_string = False
                i += 1
                continue
            
            if ch == '{': brace_count += 1
            elif ch == '}': brace_count -= 1
            i += 1
        return i - 1

    def _extract_classes(self):
        class_pattern = r'(?:abstract\s+|final\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?\s*\{'
        for match in re.finditer(class_pattern, self.code):
            class_name = match.group(1)
            extends = match.group(2)
            start_pos = match.end()
            end_pos = self._find_matching_brace(start_pos)
            body = self.code[start_pos:end_pos]

            cls = ClassInfo(
                name=class_name,
                short_name=class_name,
                parent_class=extends
            )
            
            cls.properties = self._extract_properties(body)
            cls.methods = self._extract_methods(body, match.start())
            
            self.classes.append(cls)
            self.class_map[class_name] = cls

    def _extract_properties(self, body: str) -> Dict[str, PropertyInfo]:
        props = {}
        pattern = r'(public|protected|private)(?:\s+static)?\s+\$(\w+)(?:\s*=\s*([^;]+))?;'
        for m in re.finditer(pattern, body):
            vis, name, default = m.group(1), m.group(2), m.group(3)
            props[name] = PropertyInfo(
                name=name,
                visibility=vis,
                default_value=default.strip() if default else None
            )
        return props

    def _extract_methods(self, body: str, class_start: int) -> Dict[str, MethodInfo]:
        methods = {}
        # 修复：支持返回类型声明（如 : array, : void）
        pattern = r'(?:public|protected|private)?\s*(?:static\s+)?function\s+(\w+)\s*\([^\)]*\)(?:\s*:\s*\w+)?\s*\{'
        for m in re.finditer(pattern, body):
            name = m.group(1)
            # 计算绝对位置以处理嵌套括号
            abs_start = class_start + (m.start() + len(m.group(0)) - 1)
            abs_end = self._find_matching_brace(abs_start)
            
            # 提取方法体（去掉最外层花括号）
            method_body = self.code[abs_start + 1 : abs_end].strip()
            
            methods[name] = MethodInfo(
                name=name,
                body=method_body
            )
        return methods

    def _merge_inheritance(self):
        for cls in self.classes:
            if cls.parent_class and cls.parent_class in self.class_map:
                parent = self.class_map[cls.parent_class]
                # 简单的属性/方法合并逻辑，子类优先
                for k, v in parent.all_properties.items():
                    if k not in cls.all_properties:
                        cls.all_properties[k] = v
                for k, v in parent.all_methods.items():
                    if k not in cls.all_methods:
                        cls.all_methods[k] = v
            # 合并自身属性和方法
            cls.all_properties.update(cls.properties)
            cls.all_methods.update(cls.methods)
