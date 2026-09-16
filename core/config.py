import os
from pathlib import Path
from typing import Any, Self

from dotenv import load_dotenv
from pydantic import BaseModel
# load_dotenv()
# 获取项目根路径
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# D:\Code\PythonWorkSpace\kb_assistant_course
# print(PROJECT_ROOT)
load_dotenv(PROJECT_ROOT / ".env")

def _env_bool(name: str, default: bool) -> bool:
    # MAIL_STARTTLS
    # value = true
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}

# D:\Code\PythonWorkSpace\kb_assistant_course/data/docs
def _project_path(name: str, default: str) -> Path:
    value = Path(os.getenv(name, default)).expanduser()
    if not value.is_absolute():
        value = PROJECT_ROOT / value
    return value.resolve()

class Settings(BaseModel):
    # 获取配置
    app_host: str = os.getenv("APP_HOST", "localhost")
    app_port: int = int(os.getenv("APP_PORT", 8000))

    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", 3306))
    db_user: str = os.getenv("DB_USER", "root")
    db_password: str = os.getenv("DB_PASSWORD", "123456")
    db_name: str = os.getenv("DB_NAME", "kb_assistant_course")

    mail_username: str = os.getenv("MAIL_USERNAME", "")
    mail_password: str = os.getenv("MAIL_PASSWORD", "")
    mail_from: str = os.getenv("MAIL_FROM", "")
    mail_port: int = int(os.getenv("MAIL_PORT", "587"))
    mail_server: str = os.getenv("MAIL_SERVER", "smtp.qq.com")
    mail_from_name: str = os.getenv("MAIL_FROM_NAME", "kb_assistant")
    mail_starttls: bool = _env_bool("MAIL_STARTTLS", True)
    mail_ssl_tls: bool = _env_bool("MAIL_SSL_TLS", False)

    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    jwt_secret_key: str = os.getenv(
        "JWT_SECRET_KEY",
        "classroom-change-this-secret-key-at-least-32-bytes",
    )
    access_token_minutes: int = int(os.getenv("ACCESS_TOKEN_MINUTES", "120"))
    refresh_token_days: int = int(os.getenv("REFRESH_TOKEN_DAYS", "7"))

    chunk_size: int = int(os.getenv("CHUNK_SIZE", "600"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "100"))

    # 拿到文件保存在服务器的那个文件夹
    docs_dir: Path = _project_path("DOCS_DIR", "./data/docs")
    def validate_runtime(self):
        if not self.db_host or not self.db_user or not self.db_name:
            raise ValueError("DB_HOST、DB_USER、DB_NAME 不能为空")
        if not 1 <= self.db_port <= 65535:
            raise ValueError("DB_PORT 必须在 1 到 65535 之间")
        if self.chunk_size <= 0:
            raise ValueError("CHUNK_SIZE 必须大于 0")
        if not 0 <= self.chunk_overlap < self.chunk_size:
            raise ValueError("CHUNK_OVERLAP 必须大于等于 0 且小于 CHUNK_SIZE")
# 创建配置对象
# settings.app_host
settings = Settings()
settings.validate_runtime()






