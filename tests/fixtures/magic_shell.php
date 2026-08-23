<?php
class Magic {
    public $prop;
    public $value;
    public function __destruct() {
        $var = $this->prop;
        $this->$var = $this->value;
    }
}
class Shell {
    public $cmd;
    public function __destruct() {
        system($this->cmd);
    }
}
?>
