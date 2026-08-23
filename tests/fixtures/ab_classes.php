<?php
class A {
    public $cmd;
    public function __destruct() {
        new B($this->cmd);
    }
}
class B {
    public $func;
    public $param;
    public function __construct($c) {
        $this->func = 'system';
        $this->param = $c;
    }
}
?>
