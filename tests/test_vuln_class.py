import pytest
from core_v2.engine import Sd0pEngineV2

def test_vuln_class_e2e():
    engine = Sd0pEngineV2()
    
    with open('tests/fixtures/vuln_class.php', 'r') as f:
        code = f.read()
        
    payload = engine.analyze_and_generate(code)
    
    print(f"Generated Payload: {repr(payload)}")
    
    # 验证关键点
    assert "O:4:\"Vuln\":1:{" in payload  # 1个属性，无 __wakeup
    assert "s:4:\"data\"" in payload      # data 属性存在
    assert "file:///flag" in payload      # XXE/SSRF 利用字符串
    
    print("✅ Vuln class test passed!")

if __name__ == "__main__":
    test_vuln_class_e2e()
