import subprocess
import tempfile
import os
from typing import Optional

class LocalSandbox:
    """本地 PHP 沙箱执行器"""
    
    def __init__(self, php_path: str = "php", timeout: int = 5):
        self.php_path = php_path
        self.timeout = timeout

    def execute(self, payload: str) -> dict:
        """
        执行 Payload 并返回结果
        :param payload: PHP 反序列化字符串
        :return: {"success": bool, "output": str, "error": str, "command": str}
        """
        # 构造测试脚本
        escaped_payload = payload.replace("'", "\\'")
        script = f"<?php unserialize('{escaped_payload}'); ?>"
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.php', delete=False) as f:
                f.write(script)
                temp_path = f.name
            
            cmd = [self.php_path, temp_path]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                encoding='utf-8',
                errors='ignore'
            )
            
            os.unlink(temp_path)
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout.strip(),
                "error": result.stderr.strip(),
                "command": " ".join(cmd)
            }
                
        except subprocess.TimeoutExpired:
            if os.path.exists(temp_path): os.unlink(temp_path)
            return {"success": False, "output": "", "error": f"执行超时 (>{self.timeout}s)"}
        except FileNotFoundError:
            return {"success": False, "output": "", "error": f"未找到 PHP 解释器: {self.php_path}"}
        except Exception as e:
            if os.path.exists(temp_path): os.unlink(temp_path)
            return {"success": False, "output": "", "error": str(e)}
