import pytest
from core_v2.engine import Sd0pEngineV2

def test_secret_class_e2e():
    engine = Sd0pEngineV2()
    
    with open('tests/fixtures/secret_class.php', 'r') as f:
        code = f.read()
        
    payload = engine.analyze_and_generate(code)
    
    print(f"Generated Payload: {repr(payload)}")
    
    # 验证关键点
    assert "O:6:\"Secret\":2:{" in payload  # 2个属性，无 __wakeup 绕过
    assert "\x00*\x00token" in payload      # protected 属性前缀
    assert "\x00*\x00key" in payload        # protected 属性前缀
    assert "admin" in payload               # token 值
    
    print("✅ Secret class test passed!")

if __name__ == "__main__":
    test_secret_class_e2e()
