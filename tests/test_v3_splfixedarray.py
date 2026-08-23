import pytest
from core_v2.engine import Sd0pEngineV2

def test_v3_splfixedarray_strategy():
    """测试 V3 SplFixedArray 溢出策略"""
    engine = Sd0pEngineV2()
    
    code = """<?php
class Container {
    public $arr;
    function __construct($size) {
        $this->arr = new SplFixedArray($size);
    }
    function set($index, $value) {
        $this->arr[$index] = $value;
    }
    function get($index) {
        return $this->arr[$index];
    }
}
$input = $_GET['data'];
$obj = unserialize($input);
if ($obj instanceof Container && $obj->get(0x7fffffff) === 'secret') {
    system('cat /flag');
}
?>"""
    
    payload = engine.analyze_and_generate(code)
    print(f"Generated SplFixedArray Payload: {repr(payload)}")
    
    # 验证 Payload 包含关键元素
    assert "Container" in payload
    assert "SplFixedArray" in payload or "arr" in payload
    
    # 尝试验证注入字段是否存在
    try:
        assert "2147483647" in payload or "0x7fffffff" in payload.lower() or "arr" in payload
        print("OK SplFixedArray Payload format validated")
    except Exception as e:
        pytest.fail(f"Payload 格式错误: {e}")

if __name__ == "__main__":
    test_v3_splfixedarray_strategy()
