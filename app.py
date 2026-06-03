"""SmartPlan 时间规划助手 - Flask 应用入口"""
import traceback
import datetime
import os
from flask import Flask, send_from_directory, request, jsonify
from flask.json.provider import DefaultJSONProvider
from flask_cors import CORS
from config import Config
from routes.auth_routes import auth_bp
from routes.task_routes import task_bp
from routes.review_routes import review_bp
from routes.daily_review_routes import daily_bp


class CustomJSONProvider(DefaultJSONProvider):
    """自定义 JSON 编码器，处理 PyMySQL 返回的 timedelta/date/datetime/bytes 对象"""
    @staticmethod
    def default(obj):
        if isinstance(obj, datetime.timedelta):
            total_seconds = int(obj.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        if isinstance(obj, datetime.date):
            return obj.isoformat()
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        if isinstance(obj, bytes):
            return obj.decode("utf-8", errors="replace")
        return super().default(obj)


app = Flask(__name__, static_folder="static", static_url_path="")
app.json = CustomJSONProvider(app)
CORS(app)

# 注册蓝图
app.register_blueprint(auth_bp)
app.register_blueprint(task_bp)
app.register_blueprint(review_bp)
app.register_blueprint(daily_bp)


def init_database():
    """应用启动时自动初始化数据库和表结构（首次自动建库建表）"""
    import pymysql
    try:
        # 1. 创建数据库（如果不存在）
        conn = pymysql.connect(
            host=Config.MYSQL_HOST, port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER, password=Config.MYSQL_PASSWORD,
            charset="utf8mb4",
        )
        with conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{Config.MYSQL_DATABASE}` DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_unicode_ci")
        conn.close()

        # 2. 执行建表 SQL
        conn = pymysql.connect(
            host=Config.MYSQL_HOST, port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER, password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DATABASE, charset="utf8mb4",
        )
        schema_path = os.path.join(os.path.dirname(__file__), "db", "schema.sql")
        with open(schema_path, "r", encoding="utf-8") as f:
            sql = f.read()
        with conn.cursor() as cur:
            for statement in sql.split(";"):
                stmt = statement.strip()
                if stmt and not stmt.startswith("--"):
                    if stmt.upper().startswith("CREATE DATABASE") or stmt.upper().startswith("USE "):
                        continue
                    try:
                        cur.execute(stmt)
                    except Exception:
                        pass  # 表已存在则跳过
        conn.commit()
        conn.close()
        print("✅ 数据库初始化完成")
        return True
    except Exception as e:
        print(f"⚠️  数据库初始化失败：{e}")
        print("   请确保 MySQL 已启动且 config.py 中配置正确")
        return False


@app.route("/")
def index():
    """托管前端 SPA 入口"""
    return send_from_directory("static", "index.html")


@app.route("/<path:path>")
def static_files(path):
    """托管静态文件"""
    return send_from_directory("static", path)


@app.errorhandler(404)
def not_found(e):
    """SPA fallback：非 API 路径返回 index.html"""
    if request.path.startswith("/api/"):
        return {"success": False, "message": "接口不存在", "data": None}, 404
    return send_from_directory("static", "index.html")


@app.errorhandler(500)
def internal_error(e):
    """全局 500 错误处理，返回 JSON"""
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "message": "服务器内部错误，请稍后重试", "data": None}), 500
    return jsonify({"success": False, "message": "服务器内部错误", "data": None}), 500


@app.errorhandler(Exception)
def handle_exception(e):
    """全局异常处理，API 路由返回 JSON 而非 HTML"""
    if request.path.startswith("/api/"):
        msg = str(e) if str(e) else "服务器内部错误"
        # 在 debug 模式下打印详细错误
        if Config.DEBUG:
            traceback.print_exc()
        return jsonify({"success": False, "message": msg, "data": None}), 500
    # 非 API 路径，返回 SPA 入口
    return send_from_directory("static", "index.html")


if __name__ == "__main__":
    print(f"🚀 SmartPlan 启动中...")
    print(f"   地址: http://{Config.FLASK_HOST}:{Config.FLASK_PORT}")
    print(f"   环境: {Config.FLASK_ENV}")
    init_database()
    app.run(
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        debug=Config.DEBUG,
    )
