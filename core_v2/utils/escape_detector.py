import re

class ExternalEscapeDetector:
    """外部字符串替换检测器"""

    @staticmethod
    def detect(code: str) -> list:
        """
        检测 unserialize 前的 str_replace/preg_replace 等过滤
        :return: 列表 [{"type": "str_replace", "search": "...", "replace": "...", "delta": int}]
        """
        results = []
        
        # 1. 找到所有 unserialize 的位置
        unserial_positions = [m.start() for m in re.finditer(r'unserialize\s*\(', code)]
        
        for pos in unserial_positions:
            # 截取 unserialize 前 500 个字符进行分析
            context = code[max(0, pos - 500):pos]
            
            # 2. 匹配 str_replace('a', 'b', $var) 或 str_replace("a", "b", $var)
            # 支持单引号和双引号；search/replace 允许为空字符串（如 str_replace('x', '', $var)）
            pattern = r"str_replace\s*\(\s*['\"]([^'\"]*)['\"]\s*,\s*['\"]([^'\"]*)['\"]\s*,"
            matches = re.findall(pattern, context)
            
            for search, replace in matches:
                delta = len(replace) - len(search)
                # 注意：即使 delta == 0 也要返回，因为可能是宽字节注入场景
                results.append({
                    "type": "str_replace",
                    "search": search,
                    "replace": replace,
                    "delta": delta,
                    "context": f"str_replace('{search}', '{replace}', ...)"
                })
                    
            # 3. 匹配 preg_replace('/a/', 'b', $var)
            preg_pattern = r"preg_replace\s*\(\s*['\"](/[^/]+/)['\"]\s*,\s*['\"]([^'\"]*)['\"]\s*,"
            preg_matches = re.findall(preg_pattern, context)
            for regex_pat, replace in preg_matches:
                # 简化：假设正则不改变长度，除非是固定长度替换
                results.append({
                    "type": "preg_replace",
                    "search": regex_pat,
                    "replace": replace,
                    "delta": "unknown",
                    "context": f"preg_replace('{regex_pat}', '{replace}', ...)"
                })

        return results
