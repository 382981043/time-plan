"""任务相关路由"""
from flask import Blueprint, request
from utils.response import success, fail
from utils.token import get_user_id_from_request
from services import task_service

task_bp = Blueprint("tasks", __name__, url_prefix="/api/tasks")


def _require_auth():
    user_id = get_user_id_from_request(request)
    if user_id is None:
        return None, fail("未登录或 token 已过期", status_code=401)
    return user_id, None


@task_bp.route("", methods=["GET"])
def list_tasks():
    user_id, err = _require_auth()
    if err:
        return err

    date = request.args.get("date", "").strip() or None
    status = request.args.get("status", "").strip() or None
    quadrant = request.args.get("quadrant", "").strip() or None

    tasks = task_service.get_tasks(user_id, date, status, quadrant)
    return success(tasks)


@task_bp.route("/<int:task_id>", methods=["GET"])
def get_task(task_id):
    user_id, err = _require_auth()
    if err:
        return err

    task = task_service.get_task_by_id(task_id, user_id)
    if not task:
        return fail("任务不存在", status_code=404)
    return success(task)


@task_bp.route("", methods=["POST"])
def create_task():
    user_id, err = _require_auth()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    task_date = (data.get("task_date") or "").strip()
    smart_specific = (data.get("smart_specific") or "").strip()
    smart_measurable = (data.get("smart_measurable") or "").strip()
    smart_time_bound = (data.get("smart_time_bound") or "").strip()

    # 必填校验
    missing = []
    if not title:
        missing.append("任务标题")
    if not task_date:
        missing.append("任务日期")
    if not smart_specific:
        missing.append("SMART-Specific")
    if not smart_measurable:
        missing.append("SMART-Measurable")
    if not smart_time_bound:
        missing.append("SMART-TimeBound")
    if missing:
        return fail(f"以下字段为必填：{', '.join(missing)}")

    try:
        task = task_service.create_task(user_id, data)
        return success(task, "任务创建成功")
    except Exception as e:
        return fail(str(e))


@task_bp.route("/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    user_id, err = _require_auth()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    task = task_service.update_task(task_id, user_id, data)
    if not task:
        return fail("任务不存在或无权限", status_code=404)
    return success(task, "任务更新成功")


@task_bp.route("/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    user_id, err = _require_auth()
    if err:
        return err

    deleted = task_service.delete_task(task_id, user_id)
    if not deleted:
        return fail("任务不存在或无权限", status_code=404)
    return success(None, "任务已删除")
