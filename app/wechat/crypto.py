"""微信消息加解密模块 (AES-256-CBC)"""

import base64
import hashlib
import struct
import xml.etree.ElementTree as ET

from Crypto.Cipher import AES


class WeChatCrypto:
    """微信第三方平台消息加解密"""

    def __init__(self, token: str, encoding_aes_key: str, component_appid: str):
        self.token = token
        self.component_appid = component_appid
        self.aes_key = base64.b64decode(encoding_aes_key + "=")

    def _pad(self, text: bytes) -> bytes:
        block_size = 32
        pad_len = block_size - (len(text) % block_size)
        return text + bytes([pad_len] * pad_len)

    def _unpad(self, text: bytes) -> bytes:
        pad_len = text[-1]
        return text[:-pad_len]

    def verify_signature(self, signature: str, timestamp: str, nonce: str, encrypt: str = "") -> bool:
        items = sorted([self.token, timestamp, nonce, encrypt])
        sha1 = hashlib.sha1("".join(items).encode()).hexdigest()
        return sha1 == signature

    def decrypt(self, encrypted: str) -> tuple[str, str]:
        """解密微信消息

        Returns:
            (xml_content, appid)
        """
        cipher = AES.new(self.aes_key, AES.MODE_CBC, self.aes_key[:16])
        decrypted = cipher.decrypt(base64.b64decode(encrypted))
        decrypted = self._unpad(decrypted)

        # 去除16字节随机字符串
        content = decrypted[16:]
        # 提取4字节消息长度
        msg_len = struct.unpack("!I", content[:4])[0]
        xml_content = content[4:4 + msg_len].decode("utf-8")
        appid = content[4 + msg_len:].decode("utf-8")

        return xml_content, appid

    def encrypt(self, reply_msg: str) -> str:
        """加密回复消息"""
        random_str = self._get_random_str()
        msg_bytes = reply_msg.encode("utf-8")
        appid_bytes = self.component_appid.encode("utf-8")

        text = random_str + struct.pack("!I", len(msg_bytes)) + msg_bytes + appid_bytes
        text = self._pad(text)

        cipher = AES.new(self.aes_key, AES.MODE_CBC, self.aes_key[:16])
        encrypted = base64.b64encode(cipher.encrypt(text)).decode("utf-8")
        return encrypted

    def _get_random_str(self) -> bytes:
        import os
        return os.urandom(16)


def parse_xml(xml_str: str) -> dict:
    """解析微信 XML 消息为字典"""
    root = ET.fromstring(xml_str)
    result = {}
    for child in root:
        result[child.tag] = child.text
    return result


def build_xml(data: dict) -> str:
    """构建微信 XML 消息"""
    items = []
    for key, value in data.items():
        if isinstance(value, int):
            items.append(f"<{key}>{value}</{key}>")
        else:
            items.append(f"<{key}><![CDATA[{value}]]></{key}>")
    return "<xml>" + "".join(items) + "</xml>"
