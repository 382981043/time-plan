"""AI 今日小结生成服务"""
import json
import urllib.request
import urllib.error
from config import Config
from services.db_service import execute_query


SYSTEM_PROMPT = """你是一名专业的时间管理教练。请根据用户今天的任务计划、SMART 信息、重要紧急四象限分类、完成状态和任务复盘内容，生成一份结构化的今日小结。

要求：
1. 语言简洁、具体、可执行；
2. 不要空泛鼓励；
3. 要指出具体问题；
4. 要给出明天可以执行的改进建议；
5. 输出 markdown 格式；
6. 不要编造不存在的任务；
7. 如果任务数据不足，请基于已有信息给出温和提醒。

输出格式：

## 今日整体表现

## 完成较好的地方

## 存在的问题

## 四象限时间分配分析

## SMART 计划质量分析

## 明日改进建议

## 一句话总结"""


def _build_mock_summary(tasks: list, reviews: dict, stats: dict) -> str:
    """生成 Mock 今日小结"""
    total = stats.get("total_tasks", 0)
    completed = stats.get("completed_tasks", 0)
    unfinished = stats.get("unfinished_tasks", 0)
    cancelled = stats.get("cancelled_tasks", 0)
    quadrant_stats = stats.get("quadrant_summary", {})

    if total == 0:
        return """## 今日整体表现

今天没有记录任何任务。建议即使是很小的待办事项，也记录到 SmartPlan 中，这有助于培养时间管理意识。

## 完成较好的地方

暂无数据。

## 存在的问题

今天没有任务记录，无法进行有效的时间管理分析。请确保每天至少记录 1-3 个核心任务。

## 四象限时间分配分析

暂无数据，建议关注"重要但不紧急"象限中的任务，这是长期成长的关键。

## SMART 计划质量分析

暂无数据。

## 明日改进建议

1. 明天请尝试创建至少 1 个 SMART 任务
2. 可以先从简单的任务开始，比如"整理桌面"
3. 养成每天早上列出今日任务的习惯

## 一句话总结

没有记录就没有复盘——今天是一个重新开始的好机会。"""

    lines = []
    lines.append("## 今日整体表现")
    completion_rate = f"{completed}/{total}" if total > 0 else "0/0"
    if completed > 0 and completed == total:
        lines.append(f"今天完成了全部 {total} 个任务（{completion_rate}），执行力出色！")
    elif completed > 0:
        lines.append(f"今天完成了 {completed}/{total} 个任务，完成率约 {completed * 100 // total}%。还有 {unfinished} 个任务未完成，{cancelled} 个已取消。")
    else:
        lines.append(f"今天共有 {total} 个任务，但均未完成。需要反思原因并及时调整。")
    lines.append("")

    lines.append("## 完成较好的地方")
    completed_tasks = [t for t in tasks if t.get("status") == "DONE"]
    if completed_tasks:
        for t in completed_tasks[:3]:
            lines.append(f"- 完成了「{t['title']}」")
        lines.append("")
    else:
        lines.append("今天没有标记完成的任务。建议回顾是否有部分完成但未标记的情况。")
        lines.append("")

    lines.append("## 存在的问题")
    undone_tasks = [t for t in tasks if t.get("status") in ("UNDONE", "TODO", "IN_PROGRESS")]
    if undone_tasks:
        for t in undone_tasks:
            review = reviews.get(t["id"])
            if review and review.get("problems"):
                lines.append(f"- 「{t['title']}」：{review['problems']}")
            elif review and review.get("unfinished_reason"):
                lines.append(f"- 「{t['title']}」未完成原因：{review['unfinished_reason']}")
        if not any(reviews.get(t.get("id"), {}).get("problems") or reviews.get(t.get("id"), {}).get("unfinished_reason") for t in undone_tasks):
            lines.append("- 部分未完成任务缺少复盘记录，建议为每个未完成任务记录原因")
        lines.append("")
    else:
        lines.append("无突出问题。")
        lines.append("")

    lines.append("## 四象限时间分配分析")
    q_names = {
        "IMPORTANT_URGENT": "重要且紧急",
        "IMPORTANT_NOT_URGENT": "重要但不紧急",
        "NOT_IMPORTANT_URGENT": "不重要但紧急",
        "NOT_IMPORTANT_NOT_URGENT": "不重要且不紧急",
    }
    for q_key, q_name in q_names.items():
        count = quadrant_stats.get(q_key, 0)
        if count > 0:
            lines.append(f"- {q_name}：{count} 个任务")
            if q_key == "IMPORTANT_NOT_URGENT" and count <= total * 0.3:
                lines.append('  ⚠ 建议增加"重要但不紧急"类任务的投入，这对长期发展至关重要。')
    lines.append("")

    lines.append("## SMART 计划质量分析")
    for t in tasks:
        has_specific = bool(t.get("smart_specific"))
        has_measurable = bool(t.get("smart_measurable"))
        has_timebound = bool(t.get("smart_time_bound"))
        score = sum([has_specific, has_measurable, has_timebound])
        if score < 3:
            lines.append(f"- 「{t['title']}」SMART 信息不完整，建议补充以提升计划质量")
    if all(bool(t.get("smart_specific")) and bool(t.get("smart_measurable")) and bool(t.get("smart_time_bound")) for t in tasks):
        lines.append("- 所有任务的 SMART 要素基本完整，继续保持！")
    lines.append("")

    lines.append("## 明日改进建议")
    lines.append("1. 每天早上花 5 分钟规划今日任务，确保每个任务都有明确的 SMART 目标")
    if unfinished > 0:
        lines.append(f"2. 明天优先处理今天未完成的 {unfinished} 个任务，或评估是否需要调整计划")
    if quadrant_stats.get("IMPORTANT_NOT_URGENT", 0) == 0:
        lines.append('3. 建议为明天安排至少一个"重要但不紧急"的任务，如学习或锻炼')
    lines.append("")

    lines.append("## 一句话总结")
    if completed > total * 0.7:
        lines.append("今天整体执行良好，保持节奏，明天继续关注重要事项。")
    elif completed > 0:
        lines.append("今天有进展也有遗憾，复盘今天的不足，明天更有针对性地执行。")
    else:
        lines.append("今天虽然任务完成不多，但复盘是最好的起点，明天重新出发。")

    return "\n".join(lines)


def _call_ai_api(user_content: str) -> tuple[str | None, str]:
    """调用兼容 OpenAI 格式的大模型 API，返回 (结果, 说明)"""
    if not Config.AI_API_KEY or not Config.AI_BASE_URL:
        return None, "未配置 AI_API_KEY 和 AI_BASE_URL"

    url = Config.AI_BASE_URL.rstrip("/") + "/chat/completions"
    body = json.dumps({
        "model": Config.AI_MODEL or "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.7,
        "max_tokens": 2000,
    }).encode("utf-8")

    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {Config.AI_API_KEY}")

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            content = result["choices"][0]["message"]["content"]
            return content, f"AI 生成成功（模型：{Config.AI_MODEL}）"
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        return None, f"AI 接口返回错误 {e.code}：{error_body[:200]}"
    except Exception as e:
        return None, f"AI 调用异常：{str(e)[:200]}"


def generate_daily_summary(user_id: int, date: str) -> tuple[str, str]:
    """生成今日小结，优先调用 AI，失败则返回 Mock。返回 (内容, 来源说明)"""
    # 查询当天所有任务
    tasks = execute_query(
        "SELECT * FROM tasks WHERE user_id = %s AND task_date = %s ORDER BY planned_start_time ASC",
        (user_id, date),
    )

    # 查询对应任务复盘
    reviews = {}
    for t in tasks:
        review = execute_query(
            "SELECT * FROM task_reviews WHERE task_id = %s AND user_id = %s",
            (t["id"], user_id),
            fetch_one=True,
        )
        if review:
            reviews[t["id"]] = review

    # 统计
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

    # 尝试调用 AI
    if Config.AI_API_KEY and Config.AI_BASE_URL:
        user_content_parts = []
        user_content_parts.append(f"日期：{date}")
        user_content_parts.append(f"任务总数：{stats['total_tasks']}，完成：{stats['completed_tasks']}，未完成：{stats['unfinished_tasks']}，取消：{stats['cancelled_tasks']}")
        user_content_parts.append("")
        for t in tasks:
            user_content_parts.append(f"--- 任务：{t['title']} ---")
            user_content_parts.append(f"状态：{t['status']}")
            user_content_parts.append(f"四象限：{t['quadrant']}")
            user_content_parts.append(f"S: {t.get('smart_specific', '')}")
            user_content_parts.append(f"M: {t.get('smart_measurable', '')}")
            user_content_parts.append(f"A: {t.get('smart_achievable', '')}")
            user_content_parts.append(f"R: {t.get('smart_relevant', '')}")
            user_content_parts.append(f"T: {t.get('smart_time_bound', '')}")
            review = reviews.get(t["id"])
            if review:
                user_content_parts.append(f"复盘-完成: {'是' if review.get('is_completed') else '否'}")
                user_content_parts.append(f"复盘-评分: {review.get('self_rating', 'N/A')}")
                user_content_parts.append(f"复盘-问题: {review.get('problems', '')}")
                user_content_parts.append(f"复盘-收获: {review.get('learnings', '')}")
            user_content_parts.append("")

        user_content = "\n".join(user_content_parts)
        ai_result, ai_info = _call_ai_api(user_content)
        if ai_result:
            return ai_result, ai_info
        else:
            # AI 调用失败，降级到 Mock，但仍然返回 Mock 内容
            return _build_mock_summary(tasks, reviews, stats), f"（AI 不可用：{ai_info}，已降级为本地生成）"

    # 降级到 Mock
    return _build_mock_summary(tasks, reviews, stats), "（未配置 AI，使用本地模板生成。配置 AI_API_KEY 后可调用大模型动态生成）"
