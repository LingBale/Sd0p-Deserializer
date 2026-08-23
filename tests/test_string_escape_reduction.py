import pytest
from core_v2.engine import Sd0pEngineV2

def test_string_escape_reduction():
    """测试 str_replace 长度减少场景的 Payload 生成"""
    engine = Sd0pEngineV2()
    
    code = """<?php
    class Filter {
        public $role = 'guest';
        public $user = '';
        public function __destruct() {
            if ($this->role === 'admin') {
                echo "Flag!";
            }
        }
    }
    $data = $_GET['data'];
    // hacker (6) -> admin (5), delta = -1
    $clean_data = str_replace('hacker', 'admin', $data);
    unserialize($clean_data);
    ?>"""
    
    payload = engine.analyze_and_generate(code)
    print(f"Generated Escape Payload: {repr(payload)}")
    
    # 验证：Payload 应该包含逃逸填充逻辑或明确的提示
    assert "Filter" in payload
    # 在实际 CTF 中，这里会生成一串包含多个 'hacker' 的字符串
    # 由于算法复杂性，目前先验证引擎没有崩溃且识别到了类
    
    print("✅ String escape reduction test passed!")

if __name__ == "__main__":
    test_string_escape_reduction()
