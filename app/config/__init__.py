from os import environ

from dotenv import load_dotenv

from .local import LocalDevelopmentSettings
from .production import ProductionSettings


load_dotenv()


settings_class = (
    ProductionSettings
    if environ.get("APP_ENV", "production") == "production"
    else LocalDevelopmentSettings
)

settings = settings_class()

__all__ = [
    "settings",
]
