"""密码工具 - PBKDF2-SHA256 哈希"""
import hashlib
import os
import base64


def hash_password(password: str) -> str:
    """使用 PBKDF2-SHA256 对密码进行哈希，返回格式: pbkdf2_sha256$iterations$salt$hash"""
    iterations = 260000
    salt = os.urandom(32)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    hash_b64 = base64.b64encode(dk).decode("ascii")
    salt_b64 = base64.b64encode(salt).decode("ascii")
    return f"pbkdf2_sha256${iterations}${salt_b64}${hash_b64}"


def verify_password(password: str, encoded: str) -> bool:
    """验证密码是否匹配已存储的哈希值"""
    try:
        algo, iterations, salt_b64, hash_b64 = encoded.split("$")
        if algo != "pbkdf2_sha256":
            return False
        salt = base64.b64decode(salt_b64.encode("ascii"))
        expected_hash = base64.b64decode(hash_b64.encode("ascii"))
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
        return dk == expected_hash
    except Exception:
        return False
