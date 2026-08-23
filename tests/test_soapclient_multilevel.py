import pytest
from core_v2.engine import Sd0pEngineV2

def test_soapclient_multilevel():
    """测试多级 POP 链深度追踪 (Proxy -> Task -> Execute -> SoapClient)"""
    engine = Sd0pEngineV2()
    
    code = """<?php
    class Proxy {
        public $handler;
        public function __destruct() {
            $this->handler->run();
        }
    }
    class Task {
        public $action;
        public function run() {
            $this->action->execute();
        }
    }
    class Execute {
        public $url;
        public function execute() {
            new SoapClient($this->url);
        }
    }
    ?>"""
    
    payload = engine.analyze_and_generate(code)
    print(f"Generated Multilevel Payload: {repr(payload)}")
    
    # 验证关键点
    assert "Proxy" in payload
    assert "Task" in payload
    assert "Execute" in payload
    assert "SoapClient" in payload
    assert "127.0.0.1:8080" in payload
    
    print("✅ Multilevel POP chain with SoapClient test passed!")

if __name__ == "__main__":
    test_soapclient_multilevel()
