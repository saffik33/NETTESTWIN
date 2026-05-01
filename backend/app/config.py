import json
from pathlib import Path

from pydantic_settings import BaseSettings

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/nettest.db"
    CORS_ORIGINS: str = '["http://localhost:5173"]'
    DEFAULT_PING_TARGET: str = "8.8.8.8"
    DEFAULT_DNS_TARGETS: str = '["google.com","cloudflare.com","github.com"]'
    DEFAULT_TRACEROUTE_TARGET: str = "8.8.8.8"
    SPEED_TEST_TIMEOUT: int = 60

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True
    SMTP_FROM_EMAIL: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return json.loads(self.CORS_ORIGINS)

    @property
    def dns_targets_list(self) -> list[str]:
        return json.loads(self.DEFAULT_DNS_TARGETS)

    model_config = {"env_file": str(_PROJECT_ROOT / ".env"), "extra": "ignore"}


settings = Settings()
