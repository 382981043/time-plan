"""任务相关路由"""
import json
import urllib.request
import urllib.error
from flask import Blueprint, request
from utils.response import success, fail
from utils.token import get_user_id_from_request
from services import task_service
from services.db_service import execute_query
from config import Config
from datetime import date as date_type, timedelta

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


# ========== P0: 快速添加任务 ==========

QUICK_PARSE_PROMPT = """你是一个任务解析助手。用户会用自然语言描述一个任务，你需要将其解析为结构化 JSON。

规则：
1. 提取任务标题（核心事项，不超过20字）
2. 根据描述补全 SMART 五要素，用中文
3. 推测重要性和紧急性（重要=与长期目标相关，紧急=今天必须完成）
4. 如果用户提到时间（如"下午3点""下班前""10:00"），提取为 planned_start_time 和 planned_end_time
5. task_date 默认今天
6. status 默认 TODO
7. 只返回纯 JSON，不要 markdown 代码块

返回格式：
{"title":"...","description":"...","smart_specific":"...","smart_measurable":"...","smart_achievable":"...","smart_relevant":"...","smart_time_bound":"...","important":true/false,"urgent":true/false,"planned_start_time":"HH:MM","planned_end_time":"HH:MM"}"""


def _quick_parse_with_ai(raw_text: str) -> dict | None:
    """调用 AI 解析任务描述为结构化数据"""
    if not Config.AI_API_KEY or not Config.AI_BASE_URL:
        return None
    try:
        url = Config.AI_BASE_URL.rstrip("/") + "/chat/completions"
        body = json.dumps({
            "model": Config.AI_MODEL or "deepseek-chat",
            "messages": [
                {"role": "system", "content": QUICK_PARSE_PROMPT},
                {"role": "user", "content": raw_text},
            ],
            "temperature": 0.3,
            "max_tokens": 500,
        }).encode("utf-8")
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", f"Bearer {Config.AI_API_KEY}")
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            content = result["choices"][0]["message"]["content"].strip()
            # 清理可能的 markdown 代码块
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                if content.endswith("```"):
                    content = content[:-3]
            return json.loads(content)
    except Exception:
        return None


def _quick_parse_simple(raw_text: str) -> dict:
    """简单解析（降级方案）：从文本中提取基本信息"""
    today = date_type.today().isoformat()
    # 尝试提取时间
    import re
    time_match = re.search(r'(\d{1,2}):(\d{2})', raw_text)
    start = f"{int(time_match.group(1)):02d}:{time_match.group(2)}" if time_match else None
    end = None
    if start:
        h, m = int(time_match.group(1)), int(time_match.group(2))
        end = f"{(h+1):02d}:{m:02d}"

    # 判断紧急程度
    urgent_words = ["紧急", "马上", "立刻", "赶紧", "尽快", "asap", "今天必须", "deadline", "截止"]
    important_words = ["重要", "关键", "核心", "必须完成", "重点"]
    urgent = any(w in raw_text.lower() for w in urgent_words)
    important = any(w in raw_text.lower() for w in important_words) or not urgent

    return {
        "title": raw_text[:20].strip(),
        "description": raw_text,
        "task_date": today,
        "smart_specific": raw_text[:100],
        "smart_measurable": f"完成「{raw_text[:15]}」即视为达成",
        "smart_achievable": "根据当前条件可完成",
        "smart_relevant": "与今日工作目标相关",
        "smart_time_bound": f"今天完成",
        "important": important,
        "urgent": urgent,
        "planned_start_time": start,
        "planned_end_time": end,
    }


@task_bp.route("/quick", methods=["POST"])
def quick_create():
    """快速创建任务：用户输入自然语言，AI 自动解析为结构化任务"""
    user_id, err = _require_auth()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    raw_text = (data.get("text") or "").strip()
    if not raw_text:
        return fail("请输入任务内容")

    # 1. 尝试 AI 解析
    parsed = _quick_parse_with_ai(raw_text)
    source = "AI 智能解析" if parsed is not None else "快速解析"
    # 2. 降级到简单解析
    if parsed is None:
        parsed = _quick_parse_simple(raw_text)

    # 3. 补全默认值（包括必填字段，防止 AI 返回不完整）
    parsed.setdefault("title", raw_text[:20].strip())
    parsed.setdefault("task_date", date_type.today().isoformat())
    parsed.setdefault("status", "TODO")
    parsed.setdefault("description", raw_text)
    parsed.setdefault("smart_specific", raw_text[:100])
    parsed.setdefault("smart_measurable", f"完成「{raw_text[:15]}」即视为达成")
    parsed.setdefault("smart_achievable", "")
    parsed.setdefault("smart_relevant", "")
    parsed.setdefault("smart_time_bound", "今天完成")
    parsed.setdefault("important", False)
    parsed.setdefault("urgent", False)
    parsed.setdefault("planned_start_time", None)
    parsed.setdefault("planned_end_time", None)

    try:
        task = task_service.create_task(user_id, parsed)
        return success({"task": task, "parsed_by": source}, "任务创建成功")
    except Exception as e:
        return fail(str(e))


# ========== P1: 仪表盘统计数据 ==========

@task_bp.route("/stats", methods=["GET"])
def get_stats():
    """获取仪表盘统计：完成率、连续打卡天数、本周趋势"""
    user_id, err = _require_auth()
    if err:
        return err

    today = date_type.today()

    # 今日统计
    today_str = today.isoformat()
    today_tasks = task_service.get_tasks(user_id, today_str)
    total = len(today_tasks)
    done = sum(1 for t in today_tasks if t["status"] == "DONE")

    # 连续打卡天数（有至少1个完成任务的连续天数）
    streak = 0
    check_date = today
    while True:
        tasks_on_date = task_service.get_tasks(user_id, check_date.isoformat())
        if any(t["status"] == "DONE" for t in tasks_on_date):
            streak += 1
            check_date -= timedelta(days=1)
        else:
            # 今天还没完成不算断
            if check_date == today:
                check_date -= timedelta(days=1)
                continue
            break

    # 本周统计（周一到今天）
    monday = today - timedelta(days=today.weekday())
    week_data = []
    for i in range(7):
        d = monday + timedelta(days=i)
        if d > today:
            break
        tasks = task_service.get_tasks(user_id, d.isoformat())
        t = len(tasks)
        c = sum(1 for tk in tasks if tk["status"] == "DONE")
        week_data.append({
            "date": d.isoformat(),
            "weekday": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][d.weekday()],
            "total": t,
            "done": c,
            "rate": round(c / t * 100) if t > 0 else 0,
        })

    # 本周总完成率
    week_total = sum(w["total"] for w in week_data)
    week_done = sum(w["done"] for w in week_data)
    week_rate = round(week_done / week_total * 100) if week_total > 0 else 0

    return success({
        "today": {"total": total, "done": done, "rate": round(done / total * 100) if total > 0 else 0},
        "streak": streak,
        "week": {"total": week_total, "done": week_done, "rate": week_rate, "days": week_data},
    })


# ========== 优化1: 快捷状态更新 ==========

@task_bp.route("/<int:task_id>/status", methods=["PATCH"])
def update_task_status(task_id):
    """快捷更新任务状态：开始 / 完成 / 取消"""
    user_id, err = _require_auth()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    new_status = (data.get("status") or "").strip().upper()
    valid_statuses = ["TODO", "IN_PROGRESS", "DONE", "UNDONE", "CANCELLED"]
    if new_status not in valid_statuses:
        return fail(f"无效状态，可选值：{', '.join(valid_statuses)}")

    task = task_service.get_task_by_id(task_id, user_id)
    if not task:
        return fail("任务不存在或无权限", status_code=404)

    task_service.update_task(task_id, user_id, {"status": new_status})
    updated = task_service.get_task_by_id(task_id, user_id)
    return success(updated, f"任务已标记为{new_status}")


# ========== 优化2: 昨日未完成任务迁移 ==========

@task_bp.route("/yesterday-unfinished", methods=["GET"])
def yesterday_unfinished():
    """获取昨日未完成的任务列表"""
    user_id, err = _require_auth()
    if err:
        return err

    yesterday = (date_type.today() - timedelta(days=1)).isoformat()
    tasks = task_service.get_tasks(user_id, yesterday)
    # 筛选未完成状态
    unfinished = [t for t in tasks if t["status"] in ("TODO", "IN_PROGRESS", "UNDONE")]
    return success({"date": yesterday, "tasks": unfinished, "count": len(unfinished)})


@task_bp.route("/<int:task_id>/migrate", methods=["POST"])
def migrate_task(task_id):
    """将任务迁移到今天（复制一份，保留 SMART 信息）"""
    user_id, err = _require_auth()
    if err:
        return err

    task = task_service.get_task_by_id(task_id, user_id)
    if not task:
        return fail("任务不存在或无权限", status_code=404)

    today = date_type.today().isoformat()
    # 如果任务已经是今天的，不需要迁移
    if str(task.get("task_date")) == today:
        return fail("该任务已经是今天的")

    new_data = {
        "title": task["title"],
        "description": task.get("description", ""),
        "task_date": today,
        "planned_start_time": task.get("planned_start_time"),
        "planned_end_time": task.get("planned_end_time"),
        "status": "TODO",
        "smart_specific": task["smart_specific"],
        "smart_measurable": task["smart_measurable"],
        "smart_achievable": task.get("smart_achievable", ""),
        "smart_relevant": task.get("smart_relevant", ""),
        "smart_time_bound": task["smart_time_bound"],
        "important": bool(task.get("important")),
        "urgent": bool(task.get("urgent")),
    }
    new_task = task_service.create_task(user_id, new_data)
    return success(new_task, "任务已迁移到今天")
