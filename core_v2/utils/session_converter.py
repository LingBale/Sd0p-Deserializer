import re
import base64
import pickle
from urllib.parse import quote, unquote

class SessionConverter:
    """PHP Session 格式转换器
    
    支持三种 PHP Session 序列化引擎格式互转：
    - php: key|value 格式（默认引擎）
    - php_serialize: a:1:{s:key_len:"key";value;} 格式
    - php_binary: \x03key + value_len字节 + value 格式
    """

    @staticmethod
    def php_to_serialize(session_str):
        """将 php 格式转换为 php_serialize 格式
        
        Args:
            session_str: php 格式字符串，如 'user|O:4:"Test":1:{s:4:"name";s:5:"admin";}'
        
        Returns:
            php_serialize 格式字符串，如 'a:1:{s:4:"user";O:4:"Test":1:{s:4:"name";s:5:"admin";}}'
        
        Raises:
            ValueError: 输入格式不正确时抛出异常
        """
        if '|' not in session_str:
            raise ValueError("Invalid php session format: missing '|' separator")
        
        # 分割 key 和 value（只分割第一个 |）
        key, value = session_str.split('|', 1)
        
        if not key or not value:
            raise ValueError("Invalid php session format: empty key or value")
        
        key_len = len(key)
        return f'a:1:{{s:{key_len}:"{key}";{value}}}'

    @staticmethod
    def serialize_to_php(serialized_str):
        """将 php_serialize 格式转换为 php 格式
        
        Args:
            serialized_str: php_serialize 格式字符串，如 'a:1:{s:4:"user";O:4:"Test":1:{s:4:"name";s:5:"admin";}}'
        
        Returns:
            php 格式字符串，如 'user|O:4:"Test":1:{s:4:"name";s:5:"admin";}'
        
        Raises:
            ValueError: 输入格式不支持时抛出异常
        """
        # 使用正则提取数组内部的 key 和 value
        # 匹配模式：a:1:{s:<len>:"<key>";<value>}
        match = re.match(r'^a:1:\{s:(\d+):"([^"]+)";(.+)\}$', serialized_str)
        
        if not match:
            raise ValueError(f"Unsupported php_serialize format: {serialized_str[:50]}...")
        
        key_len, key, value = match.groups()
        
        # 验证长度是否一致
        if int(key_len) != len(key):
            raise ValueError(f"Key length mismatch: expected {key_len}, got {len(key)}")
        
        return f"{key}|{value}"

    @staticmethod
    def to_binary(serialized_str, key="key"):
        """将序列化字符串转换为 php_binary 格式
        
        Args:
            serialized_str: 任意序列化字符串，如 'O:4:"Test":0:{}'
            key: Session 键名，默认为 'key'
        
        Returns:
            php_binary 格式的二进制字符串
            格式：\x03<key><value_len_byte><value>
            例如：\x03key\x0fO:4:"Test":0:{}
        
        Raises:
            ValueError: 输入为空时抛出异常
        """
        if not serialized_str:
            raise ValueError("Input serialized string cannot be empty")
        
        key_len = len(key)
        value_len = len(serialized_str)
        
        # php_binary 格式：
        # 1. 键名长度（1字节）+ 键名
        # 2. 值长度（1字节）+ 值
        # 注意：这里简化处理，假设长度 < 256
        if key_len >= 256 or value_len >= 256:
            raise ValueError("Key or value too long for binary format (must be < 256 bytes)")
        
        # 构建二进制字符串
        binary_str = chr(key_len) + key + chr(value_len) + serialized_str
        
        return binary_str
