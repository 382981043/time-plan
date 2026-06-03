"""认证相关路由"""
from flask import Blueprint, request
from utils.response import success, fail
from utils.token import get_user_id_from_request
from services import auth_service

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip()
    password = (data.get("password") or "").strip()

    if not username or not email or not password:
        return fail("用户名、邮箱和密码不能为空")
    if len(password) < 6:
        return fail("密码长度不能少于 6 位")

    try:
        user = auth_service.register_user(username, email, password)
        return success(user, "注册成功")
    except ValueError as e:
        return fail(str(e))
    except Exception as e:
        return fail(f"服务器错误：{str(e)}", status_code=500)


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    password = (data.get("password") or "").strip()

    if not email or not password:
        return fail("邮箱和密码不能为空")

    try:
        result = auth_service.login_user(email, password)
        return success(result, "登录成功")
    except ValueError as e:
        return fail(str(e))
    except Exception as e:
        return fail(f"服务器错误：{str(e)}", status_code=500)


@auth_bp.route("/me", methods=["GET"])
def me():
    user_id = get_user_id_from_request(request)
    if user_id is None:
        return fail("未登录或 token 已过期", status_code=401)

    user = auth_service.get_user_by_id(user_id)
    if user is None:
        return fail("用户不存在", status_code=404)

    return success(user)
