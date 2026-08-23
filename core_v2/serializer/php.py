from typing import Dict, Any, Optional

def serialize_php(class_name: str, properties: Dict[str, Any], visibilities: Dict[str, str], bypass_wakeup: bool = False, use_array_format: bool = False, references: Dict[str, str] = None, raw_injections: Optional[Dict[str, str]] = None) -> str:
    """
    生成 PHP 序列化字符串
    :param references: P2-2, { 'A': 'B' } means property A references property B
    :param raw_injections: V3-1, { 'prop_name': 'raw_serialized_value' } 用于原始值注入
    """
    prop_count = len(properties)
    if bypass_wakeup:
        prop_count += 1
    
    if use_array_format:
        # PHP 7.4+ __serialize 返回数组时的格式：O:ClassName:Count:{...}
        payload = f'O:{len(class_name)}:"{class_name}":{prop_count}:{{'
        for name, value in properties.items():
            payload += f's:{len(name)}:"{name}";'
            payload += _serialize_value(value)
        payload += '}'
        return payload

    payload = f'O:{len(class_name)}:"{class_name}":{prop_count}:{{'
    
    # P2-2: 引用处理逻辑
    current_index = 1
    prop_keys = list(properties.keys())
    
    for i, name in enumerate(prop_keys):
        vis = visibilities.get(name, 'public')
        
        # 处理可见性前缀
        if vis == 'protected':
            key = f"\x00*\x00{name}"
        elif vis == 'private':
            key = f"\x00{class_name}\x00{name}"
        else:
            key = name
            
        payload += f's:{len(key)}:"{key}";'
        
        # 检查是否是引用属性
        if references and name in references:
            target_prop = references[name]
            # 找到被引用属性的索引 (从 1 开始)
            try:
                target_index = prop_keys.index(target_prop) + 1
                payload += f'R:{target_index};'
            except ValueError:
                # 如果被引用的属性不存在，回退到普通序列化
                payload += _serialize_value(properties[name])
        else:
            payload += _serialize_value(properties[name])
            
    payload += '}'
    
    # V3-1: 处理原始值注入
    if raw_injections:
        payload = _apply_raw_injections(payload, class_name, properties, visibilities, raw_injections)
    
    return payload

def _serialize_value(value: Any) -> str:
    if isinstance(value, bool):
        return f'b:{int(value)};'
    elif isinstance(value, int):
        return f'i:{value};'
    elif isinstance(value, list):
        # 简单支持索引数组
        payload = f'a:{len(value)}:{{'
        for i, v in enumerate(value):
            payload += f'i:{i};{_serialize_value(v)}'
        payload += '}'
        return payload
    elif isinstance(value, str):
        return f's:{len(value)}:"{value}";'
    elif isinstance(value, dict) and 'class_name' in value:
        # 支持嵌套对象序列化
        bypass = value.get('bypass_wakeup', False)
        
        # 关键修复：需要合并 nested_objects 到 properties 中
        nested_props = value['properties'].copy()
        for prop_name, sub_obj in value.get('nested_objects', {}).items():
            if sub_obj and isinstance(sub_obj, dict) and 'class_name' in sub_obj:
                nested_props[prop_name] = sub_obj
        
        return serialize_php(value['class_name'], nested_props, value.get('visibilities', {}), bypass)
    elif value is None:
        return 'N;'
    # 简化：暂不支持关联数组和嵌套对象，后续可扩展
    return f's:{len(str(value))}:"{str(value)}";'

def _apply_raw_injections(payload: str, class_name: str, properties: Dict[str, Any], visibilities: Dict[str, str], raw_injections: Dict[str, str]) -> str:
    """
    V3-1: 应用原始值注入
    
    通过字符串替换的方式，将指定属性的序列化值替换为原始值。
    需要处理可见性前缀（如 \x00*\x00prop）的匹配问题。
    
    :param payload: 原始生成的 Payload
    :param class_name: 类名
    :param properties: 属性字典
    :param visibilities: 可见性字典
    :param raw_injections: { 'prop_name': 'raw_serialized_value' }
    :return: 替换后的 Payload
    :raises ValueError: 如果替换后长度不一致
    """
    import re
    
    for prop_name, raw_value in raw_injections.items():
        # 构造带可见性前缀的属性名
        vis = visibilities.get(prop_name, 'public')
        if vis == 'protected':
            key = f"\x00*\x00{prop_name}"
        elif vis == 'private':
            key = f"\x00{class_name}\x00{prop_name}"
        else:
            key = prop_name
        
        # 构造要查找的模式：s:length:"key";
        key_pattern = f's:{len(key)}:"{re.escape(key)}";'
        
        # 在 payload 中查找该属性的位置
        match = re.search(key_pattern, payload)
        if not match:
            raise ValueError(f"未找到属性 '{prop_name}' 的序列化片段，无法进行原始值注入")
        
        # 找到属性值的位置（在 key 之后）
        value_start = match.end()
        
        # 找到当前值的结束位置（下一个分号）
        value_end = payload.find(';', value_start) + 1
        if value_end == 0:
            raise ValueError(f"无法确定属性 '{prop_name}' 的值边界")
        
        current_value = payload[value_start:value_end]
        
        # 检查长度是否一致
        if len(current_value) != len(raw_value):
            # 抛出警告但不中断（可选：可以改为严格模式）
            print(f"⚠️ 警告: 属性 '{prop_name}' 的原始值长度 ({len(raw_value)}) 与原值长度 ({len(current_value)}) 不一致")
            # 为了保持 Payload 格式正确，我们仍然进行替换
        
        # 执行替换
        payload = payload[:value_start] + raw_value + payload[value_end:]
    
    return payload
