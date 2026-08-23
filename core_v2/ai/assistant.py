from typing import List, Dict, Any
from ..model.class_info import ClassInfo, FeatureSet

class AIAnalyzer:
    """基于规则的 AI 安全审计助手"""

    def analyze(self, class_info: ClassInfo, features: FeatureSet) -> List[Dict[str, str]]:
        risks = []
        
        # 1. 危险魔术方法检测
        if features.has_wakeup and features.has_destruct:
            risks.append({
                "level": "高危",
                "title": "发现 __wakeup 与 __destruct 共存",
                "desc": "可能存在通过修改属性计数绕过 __wakeup 的逻辑。"
            })

        # 2. 危险函数调用检测
        dangerous_funcs = ['system', 'exec', 'passthru', 'shell_exec', 'eval', 'assert']
        for method in class_info.methods.values():
            for func in dangerous_funcs:
                if func in method.body:
                    risks.append({
                        "level": "严重",
                        "title": f"检测到危险函数: {func}",
                        "desc": f"在方法 {method.name} 中发现了 {func} 调用，可能导致 RCE。"
                    })

        # 3. MD5 弱比较检测
        if features.md5_weak_conditions:
            risks.append({
                "level": "中危",
                "title": "存在 MD5 弱比较漏洞",
                "desc": "代码中存在 md5() == '0e...' 模式，可通过魔法哈希碰撞绕过。"
            })

        # 4. 内置类实例化检测
        if features.builtin_class_conditions:
            for cond in features.builtin_class_conditions:
                risks.append({
                    "level": "高危",
                    "title": f"内置类利用: {cond.get('class_name')}",
                    "desc": "检测到敏感内置类实例化，可能触发 SSRF 或 XXE。"
                })

        # 5. 字符串逃逸检测
        if features.string_escape_conditions:
            risks.append({
                "level": "高危",
                "title": "检测到字符串逃逸场景",
                "desc": "unserialize 前存在 str_replace，且替换后长度增加，可构造注入 Payload。"
            })

        # 6. unserialize 入口检测
        if 'unserialize' in class_info.methods.get('__construct', type('obj', (), {'body': ''})()).body if '__construct' in class_info.methods else False:
             risks.append({
                "level": "中危",
                "title": "构造函数中存在 unserialize 调用",
                "desc": "如果构造函数参数可控，可能导致反序列化漏洞。"
            })

        # 7. 敏感操作检测 (__destruct)
        sensitive_ops = ['unlink', 'fopen', 'PDO', 'mysqli']
        if '__destruct' in class_info.methods:
            body = class_info.methods['__destruct'].body
            for op in sensitive_ops:
                if op in body:
                    risks.append({
                        "level": "中危",
                        "title": f"__destruct 中存在敏感操作: {op}",
                        "desc": "对象销毁时可能触发文件删除或数据库查询。"
                    })

        # 8. 废弃函数检测
        if 'preg_replace' in str([m.body for m in class_info.methods.values()]):
            risks.append({
                "level": "低危",
                "title": "检测到 preg_replace 使用",
                "desc": "若配合 /e 标志可能导致代码执行，且该用法在 PHP 7+ 已废弃。"
            })

        return sorted(risks, key=lambda x: {"严重": 0, "高危": 1, "中危": 2, "低危": 3}.get(x['level'], 4))
