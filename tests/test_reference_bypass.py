import pytest
from core_v2.engine import Sd0pEngineV2

def test_reference_bypass():
    """测试引用属性 R: 序列化支持"""
    engine = Sd0pEngineV2()
    
    code = """<?php
    class Secure {
        public $password;
        public $token;
        
        function __wakeup() {
            if ($this->token !== sha1($this->password)) {
                die("Invalid token");
            }
        }
    }
    $data = $_GET['data'];
    $obj = unserialize($data);
    if ($obj->token === sha1($obj->password)) {
        echo file_get_contents("/flag");
    }
    ?>"""
    
    payload = engine.analyze_and_generate(code)
    print(f"Generated Reference Payload: {repr(payload)}")
    
    # 验证关键点
    assert "Secure" in payload
    # 验证是否包含 R: 标记 (引用第二个属性)
    assert "R:2;" in payload or "R:1;" in payload
    
    print("✅ Reference bypass test passed!")

if __name__ == "__main__":
    test_reference_bypass()
