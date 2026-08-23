import pytest
from core_v2.engine import Sd0pEngineV2

def test_native_class_xxe():
    """测试无自定义类时的 XXE Payload 生成"""
    engine = Sd0pEngineV2()
    
    # 模拟一个只有 echo 和 unserialize 的场景
    code = """<?php
    $data = $_GET['data'];
    $obj = unserialize($data);
    echo $obj;
    ?>"""
    
    payload = engine.analyze_and_generate(code)
    print(f"Generated Native Payload: {repr(payload)}")
    
    assert "SimpleXMLElement" in payload
    assert "file:///flag" in payload or "file:///etc/passwd" in payload
    print("✅ Native class XXE generation test passed!")

def test_native_class_ssrf():
    """测试无自定义类时的 SSRF Payload 生成"""
    engine = Sd0pEngineV2()
    
    # 模拟文件读取场景
    code = """<?php
    $data = $_GET['data'];
    $obj = unserialize($data);
    file_get_contents($obj->url);
    ?>"""
    
    payload = engine.analyze_and_generate(code)
    print(f"Generated Native Payload: {repr(payload)}")
    
    assert "SoapClient" in payload
    print("✅ Native class SSRF generation test passed!")

if __name__ == "__main__":
    test_native_class_xxe()
    test_native_class_ssrf()
