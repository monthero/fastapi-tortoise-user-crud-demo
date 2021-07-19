from uuid import uuid4

from tortoise.fields import CharField, DatetimeField, UUIDField
from tortoise.models import Model


class User(Model):
    id = UUIDField(pk=True, default=uuid4)
    username = CharField(max_length=24, unique=True)
    first_name = CharField(max_length=30)
    last_name = CharField(max_length=60)
    password = CharField(max_length=128)
    created_at = DatetimeField(auto_now_add=True)
    modified_at = DatetimeField(auto_now=True)
    deleted_at = DatetimeField(null=True)
    profile_image = CharField(max_length=255)

    class PydanticMeta:
        exclude = ["password", "deleted_at"]
