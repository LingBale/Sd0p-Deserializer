import os
import hashlib
import struct

class PharGenerator:
    """PHAR 归档文件生成器"""

    def __init__(self):
        self.stub = "<?php __HALT_COMPILER(); ?>"
        self.metadata = ""
        self.payload = ""

    def set_stub(self, stub):
        self.stub = stub if stub else "<?php __HALT_COMPILER(); ?>"

    def set_metadata(self, metadata):
        self.metadata = metadata

    def set_payload(self, payload):
        self.payload = payload

    def generate(self, output_path="output.phar"):
        """
        生成 PHAR 文件
        结构: Stub + Manifest + File Content + Metadata + Signature
        """
        # 1. 构造简单的 Manifest (简化版，仅包含一个虚拟文件)
        # Manifest 长度占位
        manifest_len = 0 
        num_files = 1
        api_version = 0x110000
        flags = 0x00001000 # GF_COMPRESSED_NONE
        
        # 虚拟文件名
        filename = "payload.txt"
        filename_len = len(filename)
        
        # 计算 Manifest 内容
        manifest = struct.pack("<L", num_files)
        manifest += struct.pack("<L", api_version)
        manifest += struct.pack("<L", flags)
        manifest += struct.pack("<L", len(self.metadata))
        manifest += struct.pack("<L", 0) # Alias length
        
        # 文件条目
        crc32_val = 0
        comp_size = len(self.payload)
        uncomp_size = len(self.payload)
        
        manifest += struct.pack("<L", filename_len)
        manifest += filename.encode('utf-8')
        manifest += struct.pack("<L", crc32_val)
        manifest += struct.pack("<L", comp_size)
        manifest += struct.pack("<L", uncomp_size)
        manifest += struct.pack("<L", int(os.path.getmtime(__file__)) if os.path.exists(__file__) else 0) # Timestamp
        manifest += struct.pack("<L", 0) # Per-file flags

        manifest_len = len(manifest)

        # 2. 组装 PHAR 内容
        phar_content = self.stub.encode('utf-8')
        phar_content += manifest
        phar_content += self.payload.encode('utf-8')
        
        # 3. 处理元数据
        meta_bytes = self.metadata.encode('utf-8') if self.metadata else b""
        phar_content += meta_bytes

        # 4. 添加签名 (SHA-1)
        sig_data = phar_content
        signature = hashlib.sha1(sig_data).digest()
        phar_content += signature
        phar_content += struct.pack("<L", 0x00010002) # SHA-1 Signature Type
        phar_content += b"GBMB" # Magic Bytes

        with open(output_path, 'wb') as f:
            f.write(phar_content)
        
        return output_path
