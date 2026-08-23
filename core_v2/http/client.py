import requests
from urllib.parse import quote

class HttpClient:
    """V2 UI HTTP 发包工具"""

    def __init__(self):
        self.session = requests.Session()

    def send(self, url, method="GET", payload="", param_name="data", headers=None, cookies=None, timeout=5):
        """
        发送包含 Payload 的 HTTP 请求
        :return: {"status": int, "headers": dict, "body": str, "request_raw": str}
        """
        # V3 Bug补充修复: 防御性去除 data= 前缀
        if isinstance(payload, str) and payload.startswith('data='):
            payload = payload[5:]
            import logging
            logging.warning("HttpClient.send stripped 'data=' prefix from payload.")
        
        # V3 Bug修复: 防御性校验，防止传入预览注释
        if isinstance(payload, str) and payload.startswith('# Payload is usually appended to URL in GET requests:'):
            import logging
            logging.warning("HttpClient.send received preview comment instead of real payload!")
            return {"success": False, "error": "检测到预览注释文本，请检查 Payload 是否正确生成"}
        
        try:
            # V3 Bug修复: 移除手动 URL 编码，requests 库会自动处理
            # encoded_payload = quote(payload, safe='')
            
            req_headers = headers or {}
            req_cookies = cookies or {}

            if method.upper() == "GET":
                params = {param_name: payload}  # 直接使用原始 Payload，requests 会自动编码
                response = self.session.get(url, params=params, headers=req_headers, cookies=req_cookies, timeout=timeout)
            else:
                data = {param_name: payload}  # 直接使用原始 Payload，requests 会自动编码
                response = self.session.post(url, data=data, headers=req_headers, cookies=req_cookies, timeout=timeout)

            # 构造原始请求字符串（简化版）
            raw_request = f"{method} {response.url} HTTP/1.1\n"
            for k, v in response.request.headers.items():
                raw_request += f"{k}: {v}\n"
            if method == "POST":
                raw_request += f"\n{param_name}={payload}"

            return {
                "success": True,
                "status": response.status_code,
                "headers": dict(response.headers),
                "body": response.text,
                "request_raw": raw_request
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def build_raw_request(url, method="GET", payload="", param_name="data", headers=None):
        """
        构建原始 HTTP 请求报文
        :return: 字符串格式的原始请求
        """
        from urllib.parse import urlparse, quote
        parsed = urlparse(url)
        path = parsed.path if parsed.path else "/"
        if parsed.query:
            path += f"?{parsed.query}"
        
        encoded_payload = quote(payload, safe='')
        req_headers = headers or {}
        
        # 构造请求行和头部
        raw = f"{method} {path} HTTP/1.1\r\n"
        raw += f"Host: {parsed.netloc}\r\n"
        
        for k, v in req_headers.items():
            raw += f"{k}: {v}\r\n"
        
        if method.upper() == "POST":
            raw += "Content-Type: application/x-www-form-urlencoded\r\n"
            raw += f"Content-Length: {len(f'{param_name}={encoded_payload}')}\r\n"
        
        raw += "\r\n" # 空行
        
        if method.upper() == "POST":
            raw += f"{param_name}={encoded_payload}"
        elif method.upper() == "GET" and payload:
            # 如果是 GET 且有 Payload，通常拼接到 URL，这里为了预览方便展示在 Body 位置或提示
            raw += f"# Payload is usually appended to URL in GET requests: {param_name}={encoded_payload}"
            
        return raw
