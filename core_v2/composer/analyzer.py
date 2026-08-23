import json
import os
from typing import List, Dict

class ComposerAnalyzer:
    """Composer 依赖分析器"""

    def analyze(self, directory: str) -> List[Dict[str, str]]:
        """
        分析目录下的 composer.json
        :return: 依赖列表 [{"name": "...", "version": "...", "type": "..."}]
        """
        composer_path = os.path.join(directory, "composer.json")
        if not os.path.exists(composer_path):
            raise FileNotFoundError(f"未在 {directory} 下找到 composer.json")

        try:
            with open(composer_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            raise ValueError("composer.json 格式错误")

        dependencies = []
        
        # 分析 require
        for name, version in data.get("require", {}).items():
            dependencies.append({
                "name": name,
                "version": version,
                "type": "require"
            })

        # 分析 require-dev
        for name, version in data.get("require-dev", {}).items():
            dependencies.append({
                "name": name,
                "version": version,
                "type": "require-dev"
            })

        return dependencies
