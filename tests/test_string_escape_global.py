import pytest
from core_v2.engine import Sd0pEngineV2

def test_string_escape_global_increase():
    """测试全局作用域长度增加场景 (addslashes)"""
    engine = Sd0pEngineV2()
    
    code = """<?php
    class EscapeTest {
        public $username;
        public $role = 'guest';
        public function __destruct() {
            if ($this->role === 'admin') {
                echo "Flag!";
            }
        }
    }
    $data = addslashes($_GET['data']);
    unserialize($data);
    ?>"""
    
    payload = engine.analyze_and_generate(code)
    print(f"Generated Increase Payload: {repr(payload)}")
    
    assert "EscapeTest" in payload
    # 验证是否包含逃逸填充逻辑（通常会有大量反斜杠或特定字符）
    assert "admin" in payload
    
    print("✅ Global string escape (increase) test passed!")

def test_string_escape_global_decrease():
    """测试全局作用域长度减少场景 (str_replace)"""
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
    print(f"Generated Decrease Payload: {repr(payload)}")
    
    assert "Filter" in payload
    # 验证是否包含填充串 'hacker'
    assert "hacker" in payload
    
    print("✅ Global string escape (decrease) test passed!")

if __name__ == "__main__":
    test_string_escape_global_increase()
    test_string_escape_global_decrease()
