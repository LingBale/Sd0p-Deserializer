<?php
class Vuln {
    public $data;
    public function __destruct() {
        $obj = new SimpleXMLElement($this->data, 0, true);
    }
}
?>
