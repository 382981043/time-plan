"""任务业务逻辑"""
from services.db_service import execute_query, execute_insert, execute_update


def _calc_quadrant(important: bool, urgent: bool) -> str:
    """根据重要/紧急计算四象限"""
    if important and urgent:
        return "IMPORTANT_URGENT"
    if important and not urgent:
        return "IMPORTANT_NOT_URGENT"
    if not important and urgent:
        return "NOT_IMPORTANT_URGENT"
    return "NOT_IMPORTANT_NOT_URGENT"


def get_tasks(user_id: int, date: str = None, status: str = None, quadrant: str = None) -> list:
    """获取用户任务列表，支持筛选"""
    sql = "SELECT * FROM tasks WHERE user_id = %s"
    params = [user_id]

    if date:
        sql += " AND task_date = %s"
        params.append(date)
    if status:
        sql += " AND status = %s"
        params.append(status)
    if quadrant:
        sql += " AND quadrant = %s"
        params.append(quadrant)

    sql += " ORDER BY planned_start_time ASC, created_at DESC"
    return execute_query(sql, tuple(params))


def get_task_by_id(task_id: int, user_id: int) -> dict | None:
    """获取单个任务详情"""
    return execute_query(
        "SELECT * FROM tasks WHERE id = %s AND user_id = %s",
        (task_id, user_id),
        fetch_one=True,
    )


def create_task(user_id: int, data: dict) -> dict:
    """创建新任务"""
    important = data.get("important", False)
    urgent = data.get("urgent", False)
    quadrant = _calc_quadrant(important, urgent)

    # 必填字段缺失时给出明确报错
    title = data.get("title") or ""
    task_date = data.get("task_date") or ""
    smart_specific = data.get("smart_specific") or ""
    smart_measurable = data.get("smart_measurable") or ""
    smart_time_bound = data.get("smart_time_bound") or ""
    if not title:
        raise ValueError("任务标题不能为空")
    if not task_date:
        raise ValueError("任务日期不能为空")
    if not smart_specific:
        raise ValueError("SMART-Specific 不能为空")
    if not smart_measurable:
        raise ValueError("SMART-Measurable 不能为空")
    if not smart_time_bound:
        raise ValueError("SMART-TimeBound 不能为空")

    task_id = execute_insert(
        """INSERT INTO tasks
        (user_id, title, description, task_date, planned_start_time, planned_end_time,
         status, smart_specific, smart_measurable, smart_achievable, smart_relevant,
         smart_time_bound, important, urgent, quadrant)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (
            user_id,
            title,
            data.get("description", ""),
            task_date,
            data.get("planned_start_time"),
            data.get("planned_end_time"),
            data.get("status", "TODO"),
            smart_specific,
            smart_measurable,
            data.get("smart_achievable", ""),
            data.get("smart_relevant", ""),
            smart_time_bound,
            important,
            urgent,
            quadrant,
        ),
    )
    return get_task_by_id(task_id, user_id)


def update_task(task_id: int, user_id: int, data: dict) -> dict | None:
    """编辑任务"""
    task = get_task_by_id(task_id, user_id)
    if not task:
        return None

    important = data.get("important", task["important"])
    urgent = data.get("urgent", task["urgent"])
    quadrant = _calc_quadrant(important, urgent)

    execute_update(
        """UPDATE tasks SET title=%s, description=%s, task_date=%s,
        planned_start_time=%s, planned_end_time=%s, status=%s,
        smart_specific=%s, smart_measurable=%s, smart_achievable=%s,
        smart_relevant=%s, smart_time_bound=%s,
        important=%s, urgent=%s, quadrant=%s
        WHERE id=%s AND user_id=%s""",
        (
            data.get("title", task["title"]),
            data.get("description", task.get("description", "")),
            data.get("task_date", task["task_date"]),
            data.get("planned_start_time", task.get("planned_start_time")),
            data.get("planned_end_time", task.get("planned_end_time")),
            data.get("status", task["status"]),
            data.get("smart_specific", task["smart_specific"]),
            data.get("smart_measurable", task["smart_measurable"]),
            data.get("smart_achievable", task.get("smart_achievable", "")),
            data.get("smart_relevant", task.get("smart_relevant", "")),
            data.get("smart_time_bound", task["smart_time_bound"]),
            int(important),
            int(urgent),
            quadrant,
            task_id,
            user_id,
        ),
    )
    return get_task_by_id(task_id, user_id)


def delete_task(task_id: int, user_id: int) -> bool:
    """删除任务（关联复盘一并删除，由外键 CASCADE 处理）"""
    affected = execute_update(
        "DELETE FROM tasks WHERE id = %s AND user_id = %s",
        (task_id, user_id),
    )
    return affected > 0
