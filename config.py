import os


class Config:
    """应用配置，从环境变量读取，支持直接修改默认值"""

    # Flask
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    FLASK_HOST = os.getenv("FLASK_HOST", "127.0.0.1")
    FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))

    # MySQL
    MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "mysql")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "smart_plan")

    # JWT / Token
    JWT_SECRET = os.getenv("JWT_SECRET", "please_change_this_secret")
    TOKEN_EXPIRE_HOURS = int(os.getenv("TOKEN_EXPIRE_HOURS", "168"))

    # AI 大模型配置（兼容 OpenAI 格式的 API）
    AI_API_KEY = os.getenv("AI_API_KEY", "sk-23f7337454ca4d76852fc430aec599be")
    AI_BASE_URL = os.getenv("AI_BASE_URL", "https://api.deepseek.com")
    AI_MODEL = os.getenv("AI_MODEL", "deepseek-chat")

    # 调试模式
    DEBUG = FLASK_ENV == "development"
