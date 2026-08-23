import pytest
from core_v2.engine import Sd0pEngineV2

def test_call_pop_chain():
    engine = Sd0pEngineV2()
    
    code = """
    <?php
    class A {
        private $obj;
        function __construct($obj) { $this->obj = $obj; }
        function __destruct() { $this->obj->execute(); }
    }
    class C {
        public $cmd = "id";
        function __call($name, $args) {
            system($this->cmd);
        }
    }
    ?>
    """
    payload = engine.analyze_and_generate(code)
    
    print(f"Generated Payload: {repr(payload)}")
    
    # 验证关键点
    assert "O:1:\"A\":1:{" in payload
    # 验证私有属性前缀 \x00A\x00obj
    assert "\x00A\x00obj" in payload or "s:6:\"\x00A\x00obj\"" in payload
    
    # 验证嵌套了 C 对象
    assert "O:1:\"C\":1:{" in payload
    assert "s:3:\"cmd\";s:2:\"id\";" in payload
    
    print("✅ __call POP chain test passed!")

if __name__ == "__main__":
    test_call_pop_chain()
