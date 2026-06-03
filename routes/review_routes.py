"""任务复盘相关路由"""
from flask import Blueprint, request
from utils.response import success, fail
from utils.token import get_user_id_from_request
from services import review_service, task_service

review_bp = Blueprint("reviews", __name__, url_prefix="/api/tasks")


def _require_auth():
    user_id = get_user_id_from_request(request)
    if user_id is None:
        return None, fail("未登录或 token 已过期", status_code=401)
    return user_id, None


@review_bp.route("/<int:task_id>/review", methods=["GET"])
def get_review(task_id):
    user_id, err = _require_auth()
    if err:
        return err

    # 验证任务属于当前用户
    task = task_service.get_task_by_id(task_id, user_id)
    if not task:
        return fail("任务不存在", status_code=404)

    review = review_service.get_task_review(task_id, user_id)
    return success(review)


@review_bp.route("/<int:task_id>/review", methods=["POST"])
def save_review(task_id):
    user_id, err = _require_auth()
    if err:
        return err

    # 验证任务属于当前用户
    task = task_service.get_task_by_id(task_id, user_id)
    if not task:
        return fail("任务不存在", status_code=404)

    data = request.get_json(silent=True) or {}

    # 校验 self_rating 范围
    rating = data.get("self_rating")
    if rating is not None:
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                return fail("自我评分范围为 1-5")
        except (ValueError, TypeError):
            return fail("自我评分必须为数字")

    try:
        review = review_service.save_task_review(task_id, user_id, data)
        return success(review, "复盘保存成功")
    except Exception as e:
        return fail(str(e))
