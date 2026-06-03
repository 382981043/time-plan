"""简单 Token 工具 - 基于 hmac + base64 + json"""
import hmac
import hashlib
import base64
import json
import time
from config import Config


def generate_token(user_id: int) -> str:
    """生成 token，包含 user_id 和过期时间"""
    exp = int(time.time()) + Config.TOKEN_EXPIRE_HOURS * 3600
    payload = json.dumps({"user_id": user_id, "exp": exp}, separators=(",", ":"))
    payload_b64 = base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii").rstrip("=")
    sig = hmac.new(
        Config.JWT_SECRET.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{payload_b64}.{sig}"


def verify_token(token: str) -> dict | None:
    """验证 token 并返回 payload，无效返回 None"""
    try:
        payload_b64, sig = token.split(".", 1)
        expected_sig = hmac.new(
            Config.JWT_SECRET.encode("utf-8"),
            payload_b64.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return None
        # 补回 padding
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        payload = json.loads(base64.urlsafe_b64decode(payload_b64.encode("utf-8")))
        if payload.get("exp", 0) < int(time.time()):
            return None
        return payload
    except Exception:
        return None


def get_user_id_from_request(request) -> int | None:
    """从 Flask request 中提取并验证 token，返回 user_id 或 None"""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:]
    payload = verify_token(token)
    if payload is None:
        return None
    return payload.get("user_id")
