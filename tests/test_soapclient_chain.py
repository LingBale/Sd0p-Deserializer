import pytest
from core_v2.engine import Sd0pEngineV2

def test_soapclient_chain():
    """测试 SoapClient SSRF 链式调用 Payload 生成"""
    engine = Sd0pEngineV2()
    
    code = """<?php
    class Execute {
        public $url;
        public function __destruct() {
            new SoapClient($this->url);
        }
    }
    ?>"""
    
    payload = engine.analyze_and_generate(code)
    print(f"Generated SoapClient Payload: {repr(payload)}")
    
    # 验证关键点
    assert "Execute" in payload
    assert "SoapClient" in payload
    assert "127.0.0.1:8080" in payload
    
    print("✅ SoapClient chain test passed!")

if __name__ == "__main__":
    test_soapclient_chain()
