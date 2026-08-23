import pytest
from core_v2.engine import Sd0pEngineV2

def test_v3_fiber_strategy():
    """测试 V3 Fiber 协程策略"""
    engine = Sd0pEngineV2()
    
    code = """<?php
class Task {
    public $fiber;
    function __construct($callback) {
        $this->fiber = new Fiber($callback);
    }
    function run() {
        $this->fiber->start();
    }
}
$input = $_GET['data'];
$obj = unserialize($input);
if ($obj instanceof Task) {
    $obj->run();
}
?>"""
    
    payload = engine.analyze_and_generate(code)
    print(f"Generated Fiber Payload: {repr(payload)}")
    
    # 验证 Payload 格式
    assert "Task" in payload
    assert "Fiber" in payload or "fiber" in payload.lower()
    
    # 尝试验证序列化格式是否正确（不执行，只检查格式）
    try:
        # 这里只是检查字符串格式，实际反序列化需要 PHP 8.1+ 环境
        assert payload.startswith('O:')
        assert '{' in payload and '}' in payload
        print("OK Fiber Payload format validated")
    except Exception as e:
        pytest.fail(f"Payload 格式错误: {e}")

if __name__ == "__main__":
    test_v3_fiber_strategy()
