import pytest
from core_v2.engine import Sd0pEngineV2

def test_string_escape_e2e():
    engine = Sd0pEngineV2()
    
    with open('tests/fixtures/string_escape_class.php', 'r', encoding='utf-8') as f:
        code = f.read()
        
    payload = engine.analyze_and_generate(code)
    
    print(f"Generated Payload: {repr(payload)}")
    
    # 验证关键点
    assert "O:10:\"EscapeTest\":2:{" in payload
    assert "s:8:\"username\"" in payload
    assert "xxx" in payload # 应该包含用于逃逸的填充字符
    assert "s:4:\"role\"" in payload
    assert "s:5:\"admin\"" in payload
    
    print("✅ String Escape test passed!")

if __name__ == "__main__":
    test_string_escape_e2e()
