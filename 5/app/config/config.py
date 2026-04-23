from pydantic import BaseModel,field_validator
from pathlib import Path
from typing import Literal

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)

class ApiConfig(BaseModel):
    router_key: str

class RunConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False


BASE_DIR = Path(__file__).resolve().parent.parent.parent

class DatabaseConfig(BaseModel):
    url: str
    echo: bool = True
    future: bool = True

    @field_validator("url", mode="after")
    @classmethod
    def make_url_absolute(cls, v: str) -> str:
        """
        Если в URL указан путь через ./ , мы превращаем его в абсолютный,
        чтобы SQLite не создавал базу в разных папках.
        """
        if "sqlite" in v and "./" in v:
            # Разбиваем строку по ./ и берем имя файла (test.sqlite)
            db_name = v.split("./")[-1]
            # Собираем новый абсолютный путь
            absolute_path = BASE_DIR / db_name
            return f"sqlite+aiosqlite:///{absolute_path}"
        return v


class UrlPrefix(BaseModel):
    prefix: str = "/api"
    test: str = "/test"
    posts: str = "/posts"
    recipe: str='/recipe'
    cuisine: str='/cuisine'
    users: str = "/users"
    auth: str='/auth'
    
    @property
    def bearer_token_url(self) -> str:
        # api/auth/login
        parts = (self.prefix, self.auth, "/login")
        path = "".join(parts)
        return path.removeprefix("/")

class AccessToken(BaseModel):#4
    lifetime_seconds: int = 3600
    reset_password_token_secret: str
    verification_token_secret: str

class AuthConfig(BaseModel):
    cookie_max_age: int = 3600
    cookie_secure: bool = False
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env.template", ".env"),
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="APP_CONFIG__",
    )
    run: RunConfig = RunConfig()
    url: UrlPrefix = UrlPrefix()
    db: DatabaseConfig
    auth: AuthConfig = AuthConfig()
    access_token: AccessToken
    api: ApiConfig


settings = Settings()
