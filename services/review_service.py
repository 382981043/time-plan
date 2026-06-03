"""任务复盘 & 每日复盘 业务逻辑"""
import json
from services.db_service import execute_query, execute_insert, execute_update


def get_task_review(task_id: int, user_id: int) -> dict | None:
    """获取任务复盘"""
    return execute_query(
        "SELECT * FROM task_reviews WHERE task_id = %s AND user_id = %s",
        (task_id, user_id),
        fetch_one=True,
    )


def save_task_review(task_id: int, user_id: int, data: dict) -> dict:
    """新增或更新任务复盘"""
    existing = get_task_review(task_id, user_id)

    if existing:
        execute_update(
            """UPDATE task_reviews SET actual_start_time=%s, actual_end_time=%s,
            is_completed=%s, completion_note=%s, unfinished_reason=%s,
            problems=%s, learnings=%s, improvement=%s, self_rating=%s
            WHERE id=%s AND user_id=%s""",
            (
                data.get("actual_start_time"),
                data.get("actual_end_time"),
                data.get("is_completed", False),
                data.get("completion_note", ""),
                data.get("unfinished_reason", ""),
                data.get("problems", ""),
                data.get("learnings", ""),
                data.get("improvement", ""),
                data.get("self_rating"),
                existing["id"],
                user_id,
            ),
        )
    else:
        execute_insert(
            """INSERT INTO task_reviews
            (task_id, user_id, actual_start_time, actual_end_time, is_completed,
             completion_note, unfinished_reason, problems, learnings, improvement, self_rating)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                task_id,
                user_id,
                data.get("actual_start_time"),
                data.get("actual_end_time"),
                data.get("is_completed", False),
                data.get("completion_note", ""),
                data.get("unfinished_reason", ""),
                data.get("problems", ""),
                data.get("learnings", ""),
                data.get("improvement", ""),
                data.get("self_rating"),
            ),
        )

    # 同步更新任务状态
    is_completed = data.get("is_completed", False)
    new_status = "DONE" if is_completed else "UNDONE"
    execute_update(
        "UPDATE tasks SET status = %s WHERE id = %s AND user_id = %s",
        (new_status, task_id, user_id),
    )

    return get_task_review(task_id, user_id)


def get_daily_review(user_id: int, date: str) -> dict | None:
    """获取某日复盘"""
    return execute_query(
        "SELECT * FROM daily_reviews WHERE user_id = %s AND review_date = %s",
        (user_id, date),
        fetch_one=True,
    )


def save_daily_review(user_id: int, date: str, data: dict) -> dict:
    """保存每日复盘"""
    existing = get_daily_review(user_id, date)
    quadrant_json = json.dumps(data.get("quadrant_summary", {}), ensure_ascii=False)

    if existing:
        execute_update(
            """UPDATE daily_reviews SET total_tasks=%s, completed_tasks=%s,
            unfinished_tasks=%s, cancelled_tasks=%s, quadrant_summary=%s, ai_summary=%s
            WHERE id=%s AND user_id=%s""",
            (
                data.get("total_tasks", 0),
                data.get("completed_tasks", 0),
                data.get("unfinished_tasks", 0),
                data.get("cancelled_tasks", 0),
                quadrant_json,
                data.get("ai_summary", ""),
                existing["id"],
                user_id,
            ),
        )
    else:
        execute_insert(
            """INSERT INTO daily_reviews
            (user_id, review_date, total_tasks, completed_tasks, unfinished_tasks,
             cancelled_tasks, quadrant_summary, ai_summary)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                user_id,
                date,
                data.get("total_tasks", 0),
                data.get("completed_tasks", 0),
                data.get("unfinished_tasks", 0),
                data.get("cancelled_tasks", 0),
                quadrant_json,
                data.get("ai_summary", ""),
            ),
        )

    return get_daily_review(user_id, date)
