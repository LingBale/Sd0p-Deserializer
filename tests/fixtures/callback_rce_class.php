<?php
class CallbackRCE {
    public $func;
    public $param;
    public function __destruct() {
        call_user_func($this->func, $this->param);
    }
}
?>
