import pytest
from core_v2.engine import Sd0pEngineV2

def test_lock_class_e2e():
    engine = Sd0pEngineV2()
    
    with open('tests/fixtures/lock_class.php', 'r') as f:
        code = f.read()
        
    payload = engine.analyze_and_generate(code)
    
    print(f"Generated Payload: {repr(payload)}")
    
    # 验证关键点
    assert "O:4:\"Lock\":3:{" in payload  # 3个属性（含绕过增加的1个）
    assert "b:1;" in payload              # check 应为布尔 true
    assert "secret" in payload            # secret 属性存在
    
    print("✅ Lock class test passed!")

if __name__ == "__main__":
    test_lock_class_e2e()
