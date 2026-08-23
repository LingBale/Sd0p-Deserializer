<?php
class EscapeTest {
    public $username;
    public $role;
    public function __destruct() {
        if ($this->role === 'admin') {
            echo "Success!";
        }
    }
}

// 模拟逃逸环境
$data = $_GET['data'];
$data = str_replace('x', 'yyy', $data); // x -> yyy, delta = 2
unserialize($data);
?>
