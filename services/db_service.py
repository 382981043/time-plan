"""数据库连接服务"""
import pymysql
from config import Config


def get_connection():
    """获取 MySQL 数据库连接"""
    try:
        return pymysql.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DATABASE,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False,
        )
    except pymysql.err.OperationalError as e:
        raise RuntimeError(f"数据库连接失败，请检查 MySQL 是否已启动及配置是否正确。错误详情：{e}") from e
    except Exception as e:
        raise RuntimeError(f"数据库连接异常：{e}") from e


def execute_query(sql: str, params: tuple = None, fetch_one: bool = False):
    """执行查询并返回结果"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            if fetch_one:
                return cursor.fetchone()
            return cursor.fetchall()
    finally:
        conn.close()


def execute_update(sql: str, params: tuple = None) -> int:
    """执行增删改操作，返回受影响行数"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            conn.commit()
            return cursor.rowcount
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def execute_insert(sql: str, params: tuple = None) -> int:
    """执行插入操作，返回新插入的 ID"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            conn.commit()
            return cursor.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
