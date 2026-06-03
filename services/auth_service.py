"""认证业务逻辑"""
from services.db_service import execute_query, execute_insert
from utils.password import hash_password, verify_password
from utils.token import generate_token


def register_user(username: str, email: str, password: str) -> dict:
    """注册新用户，返回用户信息"""
    # 检查邮箱是否已存在
    existing = execute_query(
        "SELECT id FROM users WHERE email = %s", (email,), fetch_one=True
    )
    if existing:
        raise ValueError("该邮箱已被注册")

    password_hash_str = hash_password(password)
    user_id = execute_insert(
        "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
        (username, email, password_hash_str),
    )
    return {"id": user_id, "username": username, "email": email}


def login_user(email: str, password: str) -> dict:
    """用户登录，返回 token 和用户信息"""
    user = execute_query(
        "SELECT id, username, email, password_hash FROM users WHERE email = %s",
        (email,),
        fetch_one=True,
    )
    if not user:
        raise ValueError("邮箱或密码错误")

    if not verify_password(password, user["password_hash"]):
        raise ValueError("邮箱或密码错误")

    token = generate_token(user["id"])
    return {
        "token": token,
        "user": {"id": user["id"], "username": user["username"], "email": user["email"]},
    }


def get_user_by_id(user_id: int) -> dict | None:
    """根据 ID 获取用户信息"""
    return execute_query(
        "SELECT id, username, email, created_at FROM users WHERE id = %s",
        (user_id,),
        fetch_one=True,
    )
