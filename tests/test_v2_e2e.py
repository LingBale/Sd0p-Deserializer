import pytest
from core_v2.engine import Sd0pEngineV2

def test_geek_challenge_e2e():
    engine = Sd0pEngineV2()
    code = """
    <?php
    class Name {
        private $username = 'nonono';
        private $password = 'yesyes';
        public function __wakeup() { $this->username = 'guest'; }
        public function __destruct() {
            if ($this->username === 'admin' && $this->password == 100) {
                echo file_get_contents('/flag');
            }
        }
    }
    ?>
    """
    payload = engine.analyze_and_generate(code)
    
    print(f"Generated Payload: {repr(payload)}")
    
    # 验证关键点
    assert "O:4:\"Name\":3:{" in payload  # 3个属性（含绕过增加的1个）
    assert "\x00Name\x00username" in payload # 私有属性前缀
    assert "admin" in payload
    assert "i:100;" in payload # 整数类型匹配

if __name__ == "__main__":
    test_geek_challenge_e2e()
