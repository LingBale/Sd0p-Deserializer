import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from core_v2.engine import Sd0pEngineV2

def test_array_string_escape_delta_zero():
    """测试数组字符串逃逸场景（delta=0）"""
    engine = Sd0pEngineV2()
    
    # 用户提供的代码：替换前后长度相同（"危险"和"安全"都是6字节）
    code = """<?php
function evil_utf8_filter($str) {
    return str_replace("危险", "安全", $str);
}
$data = serialize(['username' => $_GET['user'], 'is_admin' => false]);
$data = evil_utf8_filter($data);
$obj = unserialize($data);
if ($obj['is_admin'] === true) {
    echo file_get_contents('/flag');
}
?>"""
    
    payload = engine.analyze_and_generate(code)
    print(f"Generated Payload: {repr(payload)}")
    
    # 验证：不应包含内置类 Payload
    assert "SimpleXMLElement" not in payload, "不应返回 SimpleXMLElement"
    assert "SoapClient" not in payload, "不应返回 SoapClient"
    
    # 验证：应检测到数组逃逸场景
    assert "数组字符串逃逸" in payload or "array" in payload.lower() or "escape" in payload.lower(), \
        f"应提示数组逃逸场景，实际返回: {payload}"
    
    # 验证：应提到 delta=0 或长度不变
    assert "delta=0" in payload or "长度相同" in payload or "length" in payload.lower(), \
        f"应提示 delta=0，实际返回: {payload}"
    
    # 验证：应提供建议
    assert "宽字节" in payload or "manual" in payload.lower() or "建议" in payload, \
        f"应提供手动构造建议，实际返回: {payload}"
    
    print("✅ 数组逃逸检测通过（delta=0 场景）")


def test_array_string_escape_with_delta():
    """测试数组字符串逃逸场景（delta != 0）"""
    engine = Sd0pEngineV2()
    
    # 构造一个 delta != 0 的场景
    code = """<?php
function filter($str) {
    return str_replace("abc", "x", $str);  // delta = -2
}
$data = serialize(['username' => $_GET['user'], 'role' => 'user']);
$data = filter($data);
$obj = unserialize($data);
if ($obj['role'] === 'admin') {
    system('cat /flag');
}
?>"""
    
    payload = engine.analyze_and_generate(code)
    print(f"Generated Payload: {repr(payload)}")
    
    # 验证：不应包含内置类 Payload
    assert "SimpleXMLElement" not in payload, "不应返回 SimpleXMLElement"
    assert "SoapClient" not in payload, "不应返回 SoapClient"
    
    # 验证：应检测到逃逸场景并提到 delta
    assert "delta" in payload.lower() or "逃逸" in payload, \
        f"应提示 delta 信息，实际返回: {payload}"
    
    # 验证：应提到目标键名
    assert "role" in payload.lower(), f"应提到目标键名 role，实际返回: {payload}"
    
    print("✅ 数组逃逸检测通过（delta != 0 场景）")


def test_no_false_positive_for_normal_array():
    """测试正常数组操作不应误报"""
    engine = Sd0pEngineV2()
    
    # 正常的数组序列化，无过滤
    code = """<?php
$data = ['username' => 'admin', 'is_admin' => true];
$serialized = serialize($data);
$obj = unserialize($serialized);
echo $obj['username'];
?>"""
    
    payload = engine.analyze_and_generate(code)
    print(f"Generated Payload: {repr(payload)}")
    
    # 验证：由于没有 str_replace，应该回退到内置类 Payload
    # 或者返回其他合理的结果，但不应报错
    assert payload is not None and len(payload) > 0, "应返回非空结果"
    
    print("✅ 正常数组操作未误报")


if __name__ == "__main__":
    print("=" * 80)
    print("数组字符串逃逸测试")
    print("=" * 80 + "\n")
    
    try:
        test_array_string_escape_delta_zero()
        print()
        test_array_string_escape_with_delta()
        print()
        test_no_false_positive_for_normal_array()
        print("\n" + "=" * 80)
        print("🎉 所有测试通过！")
        print("=" * 80)
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
