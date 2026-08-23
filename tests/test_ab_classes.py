import pytest
from core_v2.engine import Sd0pEngineV2

def test_ab_classes_e2e():
    engine = Sd0pEngineV2()
    
    with open('tests/fixtures/ab_classes.php', 'r') as f:
        code = f.read()
        
    payload = engine.analyze_and_generate(code)
    
    print(f"Generated Payload: {repr(payload)}")
    
    # 验证关键点
    assert "O:1:\"A\":1:{" in payload  # 入口类 A，1个属性
    assert "s:3:\"cmd\"" in payload    # cmd 属性存在
    assert "id" in payload             # 默认命令填充
    
    print("✅ A/B classes POP chain test passed!")

if __name__ == "__main__":
    test_ab_classes_e2e()
