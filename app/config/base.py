from pathlib import Path
from secrets import token_urlsafe
from typing import Any, Dict, Optional

from pydantic import (
    BaseSettings as PydanticBaseSettings,
    PostgresDsn,
    validator,
)


class BaseSettings(PydanticBaseSettings):
    API_PREFIX: str = "/api"
    SECRET_KEY: str = token_urlsafe(32)

    UPLOAD_FOLDER: Path = (
        Path(__file__).parents[1].resolve().joinpath("media", "uploads")
    )

    POSTGRES_HOST: str
    POSTGRES_PORT: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_DB_URI: Optional[PostgresDsn] = None

    @validator("POSTGRES_DB_URI", pre=True)
    def assemble_db_connection(
        cls, v: Optional[str], values: Dict[str, Any]
    ) -> Any:
        if isinstance(v, str):
            return v

        return PostgresDsn.build(
            scheme="postgres",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_HOST", "localhost"),
            port=values.get("POSTGRES_PORT", "5432"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )

    class Config:
        case_sensitive = True
