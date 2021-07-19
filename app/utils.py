from datetime import datetime, timezone
from io import BytesIO
from mimetypes import guess_extension
from pathlib import Path
from typing import Dict, Optional, Union
from uuid import uuid4

from passlib.context import CryptContext
from PIL import Image
from requests import get as http_get

from app.config import settings
from app.db.models import User
from app.schemas import CreateUser, UpdateUser


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return password_context.hash(password)


def download_image_from_url(url: str, user_id: str) -> str:
    mime_type: str
    file_data: bytes = bytes("", encoding="utf-8")

    try:
        with http_get(url, allow_redirects=True, stream=True) as res:
            res.raise_for_status()
            mime_type = res.headers.get("content-type").lower()
            if mime_type not in [
                "image/jpeg",
                "image/png",
                "image/webp",
            ]:
                raise ValueError(
                    'Invalid mime type, only accepting: "ima'
                    'ge/jpeg", "image/png" or "image/webp"'
                )
            for chunk in res.iter_content(chunk_size=8192):
                file_data += chunk
    except Exception:
        raise ValueError(
            f'Error occurred trying to read "{url}". STATUS CODE: '
            f"{res.status_code}"
        )

    extension: Optional[str] = guess_extension(mime_type)

    if not mime_type.startswith("image") or not extension:
        raise ValueError(
            f"The thumbnail_url should represent a file with a "
            f"valid image mime type. But we detected {mime_type}."
        )

    img: Image.Image = Image.open(BytesIO(file_data))

    uploads_folder: Path = settings.UPLOAD_FOLDER.joinpath(
        "profile_images", get_utc_now().date().isoformat()
    )

    if not uploads_folder.is_dir():
        uploads_folder.mkdir(parents=True, exist_ok=True)

    resulting_image_path: Path = uploads_folder.joinpath(
        f"{user_id}{extension}"
    )
    image_absolute_path: str = str(resulting_image_path.absolute())

    if mime_type == "image/jpeg":
        img.save(
            image_absolute_path,
            "JPEG",
            quality=85,
            progressive=True,
            optimize=True,
        )
    else:
        if mime_type == "image/webp":
            img = img.convert("RGB")

        img.save(image_absolute_path, "PNG")

    return image_absolute_path.split("uploads/profile_images/")[-1]


def process_user_upsert_info(
    upsert_user: Union[CreateUser, UpdateUser],
    user: Optional[User] = None,
) -> Dict:
    user_info: Dict = upsert_user.dict(exclude_unset=True, exclude_none=True)

    if user_info.get("password"):
        user_info["password"] = get_password_hash(
            upsert_user.password.get_secret_value()
        )

    if isinstance(upsert_user, CreateUser):
        # Doing this here because I want the created image to have the same
        #  id as the user
        user_info["id"] = uuid4()

    if user_info.get("profile_image"):
        if user:
            cleanup_current_profile_picture(sub_path=user.profile_image)

        user_info["profile_image"] = download_image_from_url(
            url=user_info.get("profile_image"),
            user_id=getattr(user, "id", None) or user_info.get("id"),
        )

    return user_info


def cleanup_current_profile_picture(sub_path: str):
    uploads_folder: Path = settings.UPLOAD_FOLDER.joinpath("profile_images")
    sub_folder, image_name = sub_path.split("/")
    date_subfolder: Path = uploads_folder.joinpath(sub_folder)
    existing_image_path: Path = date_subfolder.joinpath(image_name)

    if existing_image_path.is_file():
        existing_image_path.unlink()

    # if folder is empty after deleting file, delete folder
    if sum(1 for item in uploads_folder.joinpath(sub_folder).iterdir()) == 0:
        date_subfolder.rmdir()
