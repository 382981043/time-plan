"""每日复盘相关路由"""
from flask import Blueprint, request
from utils.response import success, fail
from utils.token import get_user_id_from_request
from services import review_service, ai_service, task_service

daily_bp = Blueprint("daily", __name__, url_prefix="/api/daily-reviews")


def _require_auth():
    user_id = get_user_id_from_request(request)
    if user_id is None:
        return None, fail("未登录或 token 已过期", status_code=401)
    return user_id, None


@daily_bp.route("", methods=["GET"])
def get_daily_review():
    user_id, err = _require_auth()
    if err:
        return err

    date = request.args.get("date", "").strip()
    if not date:
        return fail("请提供日期参数 date (YYYY-MM-DD)")

    review = review_service.get_daily_review(user_id, date)
    return success(review)


@daily_bp.route("", methods=["POST"])
def save_daily_review():
    user_id, err = _require_auth()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    date = (data.get("date") or "").strip()
    if not date:
        return fail("请提供日期")

    try:
        review = review_service.save_daily_review(user_id, date, data)
        return success(review, "每日复盘保存成功")
    except Exception as e:
        return fail(str(e))


@daily_bp.route("/generate", methods=["POST"])
def generate_summary():
    user_id, err = _require_auth()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    date = (data.get("date") or "").strip()
    if not date:
        return fail("请提供日期 date (YYYY-MM-DD)")

    # 生成 AI 今日小结
    summary = ai_service.generate_daily_summary(user_id, date)

    # 查询统计信息
    tasks = task_service.get_tasks(user_id, date)
    stats = {
        "total_tasks": len(tasks),
        "completed_tasks": sum(1 for t in tasks if t["status"] == "DONE"),
        "unfinished_tasks": sum(1 for t in tasks if t["status"] in ("UNDONE", "TODO", "IN_PROGRESS")),
        "cancelled_tasks": sum(1 for t in tasks if t["status"] == "CANCELLED"),
        "quadrant_summary": {
            "IMPORTANT_URGENT": sum(1 for t in tasks if t["quadrant"] == "IMPORTANT_URGENT"),
            "IMPORTANT_NOT_URGENT": sum(1 for t in tasks if t["quadrant"] == "IMPORTANT_NOT_URGENT"),
            "NOT_IMPORTANT_URGENT": sum(1 for t in tasks if t["quadrant"] == "NOT_IMPORTANT_URGENT"),
            "NOT_IMPORTANT_NOT_URGENT": sum(1 for t in tasks if t["quadrant"] == "NOT_IMPORTANT_NOT_URGENT"),
        },
    }

    # 保存到数据库
    stats["date"] = date
    stats["ai_summary"] = summary
    daily_review = review_service.save_daily_review(user_id, date, stats)

    return success({"daily_review": daily_review, "summary": summary}, "今日小结生成成功")
