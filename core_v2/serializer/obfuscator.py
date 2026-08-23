import base64
import zlib
import codecs

class PayloadObfuscator:
    """Payload 混淆引擎"""

    @staticmethod
    def obfuscate(payload: str, method: str) -> str:
        """
        对 Payload 进行混淆处理
        :param payload: 原始序列化字符串
        :param method: 混淆方法 (base64, gzip_base64, rot13)
        :return: 混淆后的 PHP 代码字符串
        """
        if method == "base64":
            return PayloadObfuscator._obf_base64(payload)
        elif method == "gzip_base64":
            return PayloadObfuscator._obf_gzip_base64(payload)
        elif method == "rot13":
            return PayloadObfuscator._obf_rot13(payload)
        else:
            return payload

    @staticmethod
    def _obf_base64(payload: str) -> str:
        encoded = base64.b64encode(payload.encode('utf-8')).decode('utf-8')
        return f"eval(base64_decode('{encoded}'));"

    @staticmethod
    def _obf_gzip_base64(payload: str) -> str:
        compressed = zlib.compress(payload.encode('utf-8'))
        encoded = base64.b64encode(compressed).decode('utf-8')
        return f"eval(gzuncompress(base64_decode('{encoded}')));"

    @staticmethod
    def _obf_rot13(payload: str) -> str:
        encoded = codecs.encode(payload, 'rot_13')
        return f"eval(str_rot13('{encoded}'));"
