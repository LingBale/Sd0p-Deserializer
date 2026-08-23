import pytest
from core_v2.engine import Sd0pEngineV2

def test_serialize_hooks():
    """测试 PHP 7.4+ __serialize / __unserialize 钩子支持"""
    engine = Sd0pEngineV2()
    
    code = """<?php
    class User {
        public $isAdmin = false;
        public $username = 'guest';
        
        public function __serialize(): array {
            return [
                'isAdmin' => $this->isAdmin,
                'username' => $this->username
            ];
        }
        
        public function __unserialize(array $data): void {
            $this->isAdmin = $data['isAdmin'];
            $this->username = $data['username'];
        }
        
        public function __destruct() {
            if ($this->isAdmin) {
                echo "Flag!";
            }
        }
    }
    ?>"""
    
    # 1. 测试默认模式（传统对象格式）
    payload_default = engine.analyze_and_generate(code)
    print(f"Default Payload: {repr(payload_default)}")
    assert "User" in payload_default
    
    # 2. 测试强制数组模式（通过 tags 传递）
    # 注意：目前 UI 还没接上，这里手动模拟 tags
    from core_v2.parser.php_parser import PhpParserV2
    from core_v2.detector.feature_extractor import FeatureExtractorV2
    from core_v2.strategy.registry import get_strategy
    
    parser = PhpParserV2()
    extractor = FeatureExtractorV2()
    classes = parser.parse(code)
    cls = classes[0]
    features = extractor.extract(cls)
    
    strategy = get_strategy("standard")
    payload_array = strategy.generate(cls, features, ["standard", "force_array_mode"])
    print(f"Array Mode Payload: {repr(payload_array)}")
    
    # 验证数组模式下没有可见性前缀 \x00
    assert "\x00" not in payload_array
    assert "isAdmin" in payload_array
    
    print("✅ Serialize hooks test passed!")

if __name__ == "__main__":
    test_serialize_hooks()
