"""统一响应格式工具"""
from flask import jsonify


def success(data=None, message: str = "操作成功"):
    return jsonify({"success": True, "message": message, "data": data})


def fail(message: str = "操作失败", data=None, status_code: int = 400):
    return jsonify({"success": False, "message": message, "data": data}), status_code
