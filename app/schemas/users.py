from datetime import datetime
from typing import Dict, Optional, Union
from uuid import UUID

from pydantic import BaseModel, SecretStr, constr, stricturl

from .base import BaseConfig


class UsernameAlreadyInUseErrorMessage(BaseModel):
    detail: str


class DisplayUser(BaseModel):
    id: Union[UUID, str]
    username: str
    first_name: str
    last_name: str
    profile_image: str
    created_at: datetime
    modified_at: datetime

    class Config(BaseConfig):
        json_encoders: Dict = {
            datetime: lambda dt: dt.isoformat(timespec="seconds", sep="T"),
        }
        orm_mode: bool = True


class CreateUser(BaseModel):
    username: constr(min_length=2, max_length=24)
    first_name: constr(min_length=1, max_length=30)
    last_name: constr(min_length=1, max_length=60)
    password: SecretStr
    profile_image: stricturl(
        tld_required=False,
        allowed_schemes={"https"},  # noqa: F821
    )

    class Config(BaseConfig):
        pass


class UpdateUser(BaseModel):
    username: Optional[constr(min_length=2, max_length=24)]
    first_name: Optional[constr(min_length=1, max_length=30)]
    last_name: Optional[constr(min_length=1, max_length=60)]
    password: Optional[SecretStr]
    profile_image: Optional[
        stricturl(
            tld_required=False,
            allowed_schemes={"https"},  # noqa: F821
        )
    ]

    class Config(BaseConfig):
        pass
