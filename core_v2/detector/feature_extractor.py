import re
import yaml
import os
from typing import Dict, List
from ..model.class_info import ClassInfo, FeatureSet

class FeatureExtractorV2:
    def __init__(self):
        rules_path = os.path.join(os.path.dirname(__file__), 'rules.yaml')
        with open(rules_path, 'r') as f:
            self.rules = yaml.safe_load(f)

    def extract(self, class_info: ClassInfo, full_code: str = "") -> FeatureSet:
        features = FeatureSet()
        
        # 1. 基础魔术方法检测
        method_names = set(class_info.methods.keys())
        features.has_wakeup = '__wakeup' in method_names
        features.has_destruct = '__destruct' in method_names
        features.has_tostring = '__toString' in method_names
        
        # P2-1: 检测 PHP 7.4+ 序列化钩子
        class_info.has_serialize_hook = '__serialize' in method_names
        
        # 2. 分析 __destruct 方法体，提取条件
        if '__destruct' in class_info.methods:
            body = class_info.methods['__destruct'].body
            self._extract_destruct_conditions(body, features)
        
        # 3. 遍历所有方法，查找危险函数调用、new 表达式和 MD5 弱比较
        for method in class_info.methods.values():
            self._scan_method_body(method.body, features, class_info)
            
        # P2-2: 扫描全局作用域的引用赋值 (如 $obj->token = &$obj->password)
        if full_code:
            global_ref_re = r'\$\w+->(\w+)\s*=\s*&\s*\$\w+->(\w+)'
            for match in re.finditer(global_ref_re, full_code):
                features.reference_map[match.group(1)] = match.group(2)
            
            # P2-2: 扫描逻辑等价绕过 (如 token === sha1(password))
            logic_ref_re = r'\$\w+->(\w+)\s*===?\s*\w+\(\s*\$\w+->(\w+)\s*\)'
            for match in re.finditer(logic_ref_re, full_code):
                prop_a = match.group(1)
                prop_b = match.group(2)
                if prop_a != prop_b and prop_a not in features.reference_map:
                    features.reference_map[prop_a] = prop_b

        return features

    def extract_from_code(self, class_info: ClassInfo, full_code: str) -> FeatureSet:
        """从完整代码中提取特征（包括全局作用域的逻辑）"""
        features = self.extract(class_info, full_code)
        
        # 扫描全局作用域的字符串逃逸模式
        escape_re = self.rules.get('string_escape_patterns', {}).get('pattern')
        if escape_re:
            for match in re.finditer(escape_re, full_code):
                search_str = match.group(1)
                replace_str = match.group(2)
                var_name = match.group(3)
                
                delta = len(replace_str) - len(search_str)
                cond = {
                    'search': search_str,
                    'replace': replace_str,
                    'var': var_name,
                    'delta': delta,
                    'direction': 'increase' if delta > 0 else 'decrease'
                }
                # 避免重复添加（如果方法体内已经扫描到过）
                if cond not in features.string_escape_conditions:
                    features.string_escape_conditions.append(cond)
        
        # P3-1: 检测 PHAR 反序列化场景
        phar_keywords = [
            r'phar://',           # PHAR 协议
            r'\bSplFileInfo\b',   # SplFileInfo 类
            r'\bSplFileObject\b', # SplFileObject 类
            r'\bis_file\b',       # is_file 函数
            r'\bfile_exists\b',   # file_exists 函数
            r'\bmove_uploaded_file\b',  # 文件上传
            r'\b$_FILES\b',       # 文件上传变量
        ]
        
        for keyword_pattern in phar_keywords:
            if re.search(keyword_pattern, full_code):
                if 'phar_context' not in features.tags:
                    features.tags.append('phar_context')
                break
        
        # P2-6: 增强能力边界识别 - 盲区特征检测
        boundary_patterns = {
            'spl_object_storage': [r'\bSplObjectStorage\b'],
            'incomplete_class': [r'__PHP_Incomplete_Class'],
            'wide_char_escape': [r'\biconv\b', r'\bmb_convert_encoding\b', r'\butf8_decode\b', r'\butf8_encode\b'],
            'datetime_traversal': [r'new\s+DateTime\s*\(', r'\bDateTimeZone\b'],
            'spl_fixed_array': [r'\bSplFixedArray\b'],
            'superglobal_pollution': [r'\$_SERVER\[', r'\$_ENV\[', r'ini_set\s*\(\s*[\'"]session\.auto_start'],
            # V3-0: Fiber 协程检测
            'fiber': [r'\bFiber\b', r'new\s+Fiber\s*\('],
        }
        
        for tag, patterns in boundary_patterns.items():
            for pattern in patterns:
                if re.search(pattern, full_code):
                    if tag not in features.tags:
                        features.tags.append(tag)
                    break
                
        return features

    def _extract_destruct_conditions(self, body: str, features: FeatureSet):
        for rule in self.rules.get('destruct_conditions', []):
            for match in re.finditer(rule['pattern'], body):
                # 处理正则中的多个捕获组（单引号、双引号或裸值）
                value = match.group(2) or match.group(3) or match.group(4)
                
                # V3 Bug修复: 正确识别运算符
                matched_text = match.group(0)
                if '===' in matched_text:
                    operator = '==='
                elif '!==' in matched_text:
                    operator = '!=='
                elif '!=' in matched_text:
                    operator = '!='
                else:
                    operator = '=='
                
                condition = {
                    'property': match.group(1),
                    'operator': operator,
                    'value': value,
                    'type': self._infer_type(value)
                }
                features.destruct_conditions.append(condition)

    def _scan_method_body(self, body: str, features: FeatureSet, class_info=None):
        # 扫描危险函数
        all_dangerous = []
        for cat in ['rce', 'file', 'callbacks']:
            all_dangerous.extend(self.rules.get('dangerous_functions', {}).get(cat, []))
        
        for func in all_dangerous:
            if re.search(rf'\b{func}\s*\(', body):
                call = {
                    'function': func,
                    'category': self._get_category(func),
                    'line': -1
                }
                features.dangerous_calls.append(call)

        # 扫描 new 表达式
        new_re = self.rules.get('new_expressions', {}).get('pattern')
        if new_re:
            for match in re.finditer(new_re, body):
                expr = {
                    'class_name': match.group(1),
                    'property_used': match.group(2)
                }
                features.new_expressions.append(expr)

        # 扫描 MD5 弱比较
        md5_re = self.rules.get('md5_weak_comparisons', {}).get('pattern')
        if md5_re:
            for match in re.finditer(md5_re, body):
                cond = {
                    'property': match.group(1),
                    'target_hash': match.group(2)
                }
                features.md5_weak_conditions.append(cond)

        # 扫描内置类实例化 (如 SoapClient, SimpleXMLElement)
        for rule in self.rules.get('builtin_class_instantiation', []):
            for match in re.finditer(rule['pattern'], body):
                cond = {
                    'class_name': rule['class_name'],
                    'property': match.group(1),
                    'payload_value': rule['payload_value']
                }
                features.builtin_class_conditions.append(cond)

        # 扫描跨类 POP 链实例化 (如 new B($this->cmd))
        pop_re = self.rules.get('pop_chain_instantiation', {}).get('pattern')
        if pop_re:
            for match in re.finditer(pop_re, body):
                cond = {
                    'target_class': match.group(1),
                    'source_property': match.group(2)
                }
                features.pop_chain_conditions.append(cond)

        # 扫描 __call 触发模式 (如 $this->obj->execute()) 或方法调用形式的 POP 链
        call_re = r'\$this->(\w+)->(\w+)\s*\('
        for match in re.finditer(call_re, body):
            prop_name = match.group(1)
            method_name = match.group(2)
            
            # 优先尝试在所有类中寻找含有该方法的类作为 POP 链目标
            found_in_other_class = False
            if hasattr(class_info, '_all_classes_map'):
                for cls_name, cls_info_item in class_info._all_classes_map.items():
                    if method_name in cls_info_item.methods or '__call' in cls_info_item.methods:
                        cond = {
                            'target_class': cls_name,
                            'source_property': prop_name,
                            'is_method_call': True,
                            'method_name': method_name
                        }
                        features.pop_chain_conditions.append(cond)
                        found_in_other_class = True
                        break
            
            # 如果在其他类中没找到，且当前类也没定义，则可能是 __call 触发
            if not found_in_other_class and method_name not in class_info.methods and method_name != '__call':
                cond = {
                    'type': '__call_trigger',
                    'property': prop_name,
                    'method': method_name
                }
                features.callback_rce_conditions.append(cond)

        # 扫描回调 RCE 模式 (array_map / call_user_func)
        for rule in self.rules.get('callback_rce_patterns', []):
            for match in re.finditer(rule['pattern'], body):
                cond = {
                    'type': rule['type'],
                    'func_prop': match.group(rule['func_prop']),
                    'args_prop': match.group(rule['args_prop'])
                }
                features.callback_rce_conditions.append(cond)

        # 扫描字符串逃逸模式 (str_replace + unserialize)
        escape_re = self.rules.get('string_escape_patterns', {}).get('pattern')
        if escape_re:
            for match in re.finditer(escape_re, body):
                search_str = match.group(1)
                replace_str = match.group(2)
                var_name = match.group(3)
                
                delta = len(replace_str) - len(search_str)
                cond = {
                    'search': search_str,
                    'replace': replace_str,
                    'var': var_name,
                    'delta': delta,
                    'direction': 'increase' if delta > 0 else 'decrease'
                }
                features.string_escape_conditions.append(cond)

        # 扫描动态属性赋值模式: $this->$var = $this->value;
        dynamic_re = r'\$this->\$(\w+)\s*=\s*\$this->(\w+)'
        for match in re.finditer(dynamic_re, body):
            cond = {
                'prop_var': match.group(1),
                'value_prop': match.group(2)
            }
            features.dynamic_prop_assign.append(cond)

        # P2-2: 扫描引用赋值模式: $this->A = &$this->B
        ref_re = r'\$this->(\w+)\s*=\s*&\s*\$this->(\w+)'
        for match in re.finditer(ref_re, body):
            features.reference_map[match.group(1)] = match.group(2)
        
        # P2-2: 扫描逻辑等价绕过 (如 token === sha1(password))
        logic_ref_re = r'\$this->(\w+)\s*===?\s*\w+\(\s*\$this->(\w+)\s*\)'
        for match in re.finditer(logic_ref_re, body):
            prop_a = match.group(1)
            prop_b = match.group(2)
            if prop_a != prop_b and prop_a not in features.reference_map:
                features.reference_map[prop_a] = prop_b

    def _infer_type(self, val_str: str) -> str:
        if val_str.isdigit(): return "int"
        if val_str.lower() in ['true', 'false']: return "bool"
        if val_str.startswith("'") or val_str.startswith('"'): return "string"
        return "unknown"

    def _get_category(self, func: str) -> str:
        rules = self.rules.get('dangerous_functions', {})
        for cat, funcs in rules.items():
            if func in funcs:
                return cat
        return "unknown"
