import pytest
from core_v2.serializer.php import serialize_php

def test_raw_injection_normal():
    """测试正常的原始值注入"""
    properties = {'arr': None, 'other': 'value'}
    visibilities = {'arr': 'public', 'other': 'public'}
    
    raw_injections = {
        'arr': 'C:13:"SplFixedArray":10:{i:2147483647;}'
    }
    
    payload = serialize_php(
        class_name='Container',
        properties=properties,
        visibilities=visibilities,
        raw_injections=raw_injections
    )
    
    print(f"Generated Payload: {repr(payload)}")
    assert "SplFixedArray" in payload
    assert "2147483647" in payload
    print("✅ 正常注入测试通过")

def test_raw_injection_property_not_found():
    """测试未找到属性时抛出异常"""
    properties = {'other': 'value'}
    visibilities = {'other': 'public'}
    
    raw_injections = {
        'nonexistent': 'some_value'
    }
    
    with pytest.raises(ValueError, match="未找到属性"):
        serialize_php(
            class_name='Test',
            properties=properties,
            visibilities=visibilities,
            raw_injections=raw_injections
        )
    
    print("✅ 未找到属性异常测试通过")

def test_raw_injection_length_mismatch_warning():
    """测试长度不一致时的警告（不中断）"""
    properties = {'data': 'short'}
    visibilities = {'data': 'public'}
    
    # 注入一个长度不同的值
    raw_injections = {
        'data': 'this_is_much_longer_value'
    }
    
    # 应该能够成功生成，但会打印警告
    payload = serialize_php(
        class_name='Test',
        properties=properties,
        visibilities=visibilities,
        raw_injections=raw_injections
    )
    
    assert "this_is_much_longer_value" in payload
    print("✅ 长度不一致警告测试通过（已继续执行）")

if __name__ == "__main__":
    test_raw_injection_normal()
    test_raw_injection_property_not_found()
    test_raw_injection_length_mismatch_warning()
    print("\n🎉 所有 raw_injection 测试通过！")
