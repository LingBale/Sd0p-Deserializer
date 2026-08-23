<?php
class Secret {
    protected $token;
    protected $key;
    public function __destruct() {
        if ($this->token === 'admin' && md5($this->key) == '0e1234567890') {
            echo file_get_contents('/flag');
        }
    }
}
?>
