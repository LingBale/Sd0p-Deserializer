<?php
class Lock {
    public $check;
    public $secret;
    public function __wakeup() {
        $this->check = false;
    }
    public function __destruct() {
        if ($this->check === true) {
            echo $this->secret;
        }
    }
}
?>
