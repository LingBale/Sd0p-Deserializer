<?php
/**
 * V3 Payload 测试运行器
 * 用法: php test_runner.php <base64_payload>
 */

if ($argc < 2) {
    echo json_encode([
        'status' => 'error',
        'message' => 'Usage: php test_runner.php <base64_payload>'
    ]);
    exit(1);
}

$base64_payload = $argv[1];
$payload = base64_decode($base64_payload);

if ($payload === false) {
    echo json_encode([
        'status' => 'error',
        'message' => 'Invalid base64 payload'
    ]);
    exit(1);
}

$result = [
    'status' => 'success',
    'php_version' => PHP_VERSION,
    'unserialize_success' => false,
    'output' => '',
    'error' => ''
];

try {
    // 捕获输出
    ob_start();
    
    // 尝试反序列化
    $obj = @unserialize($payload);
    
    if ($obj === false && $payload !== 'b:0;') {
        $error = error_get_last();
        throw new Exception('Unserialization failed: ' . ($error['message'] ?? 'Unknown error'));
    }
    
    $result['unserialize_success'] = true;
    $result['object_type'] = gettype($obj);
    if (is_object($obj)) {
        $result['object_class'] = get_class($obj);
    }
    
    // 如果对象有可调用方法，尝试调用
    if (is_object($obj)) {
        if (method_exists($obj, 'run')) {
            $obj->run();
        } elseif (method_exists($obj, 'execute')) {
            $obj->execute();
        } elseif (method_exists($obj, 'open')) {
            $obj->open();
        } elseif (method_exists($obj, 'check')) {
            $obj->check();
        }
    }
    
    $result['output'] = ob_get_clean();
    
} catch (Throwable $e) {
    $result['status'] = 'exception';
    $result['error'] = $e->getMessage();
    $result['trace'] = $e->getTraceAsString();
    ob_end_clean();
}

echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
