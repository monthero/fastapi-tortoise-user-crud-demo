from typing import Dict

from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise

from app.config import settings


TORTOISE_ORM: Dict = {
    "connections": {"default": settings.POSTGRES_DB_URI},
    "apps": {
        "models": {
            "models": ["app.db.models", "aerich.models"],
            "default_connection": "default",
        },
    },
    "use_tz": True,
    "timezone": "UTC",
}


def init_db(app: FastAPI):
    register_tortoise(
        app,
        config=TORTOISE_ORM,
        # db_url=settings.POSTGRES_DB_URI,
        # modules={"models": ["db.models", "aerich.models"]},
        generate_schemas=True,
        add_exception_handlers=True,
    )
