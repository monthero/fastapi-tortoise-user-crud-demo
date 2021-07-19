from typing import List, Optional

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import PlainTextResponse
from tortoise.contrib.fastapi import HTTPNotFoundError
from tortoise.exceptions import IntegrityError

from app.db.exceptions import UsernameAlreadyInUseError
from app.db.models import User
from app.schemas import (
    CreateUser,
    DisplayUser,
    UpdateUser,
    UsernameAlreadyInUseErrorMessage,
)
from app.utils import get_utc_now, process_user_upsert_info


router: APIRouter = APIRouter()


@router.get("", response_model=List[DisplayUser])
async def list_users():
    return [
        DisplayUser.from_orm(user)
        for user in await User.exclude(deleted_at__not_isnull=True).all()
    ]


@router.post(
    "",
    response_model=DisplayUser,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {"model": UsernameAlreadyInUseErrorMessage}
    },
)
async def create_user(user_in: CreateUser):
    try:
        return DisplayUser.from_orm(
            await User.create(**process_user_upsert_info(upsert_user=user_in))
        )
    except IntegrityError as e:
        if e.args[0].constraint_name != "user_username_key":
            raise e

        raise UsernameAlreadyInUseError(
            status_code=status.HTTP_409_CONFLICT,
            msg=f'The username "{user_in.username}" is already in use.',
        )


async def get_user_by_id(user_id: str) -> User:
    user: Optional[User] = await User.filter(id=user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} was not found",
        )

    if user.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} has been deleted.",
        )

    return user


@router.get(
    "/{user_id}",
    response_model=DisplayUser,
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_404_NOT_FOUND: {"model": HTTPNotFoundError}},
)
async def get_user(user_id: str):
    return DisplayUser.from_orm(await get_user_by_id(user_id))


@router.put(
    "/{user_id}",
    response_model=DisplayUser,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": HTTPNotFoundError},
        status.HTTP_409_CONFLICT: {"model": UsernameAlreadyInUseErrorMessage},
    },
)
async def update_user(user_id: str, updated_user: UpdateUser):
    user: User = await get_user_by_id(user_id)

    user = await user.update_from_dict(
        process_user_upsert_info(
            upsert_user=updated_user,
            user=user,
        )
    )
    
    try:
        await user.save()
    except IntegrityError as e:
        if e.args[0].constraint_name != "user_username_key":
            raise e

        raise UsernameAlreadyInUseError(
            status_code=status.HTTP_409_CONFLICT,
            msg=f'The username "{updated_user.username}" is already in use.',
        )

    return DisplayUser.from_orm(user)


@router.delete(
    "/{user_id}",
    responses={status.HTTP_404_NOT_FOUND: {"model": HTTPNotFoundError}},
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user(user_id: str):
    user = await get_user_by_id(user_id)
    user.deleted_at = get_utc_now()
    await user.save(update_fields=["deleted_at"])

    return PlainTextResponse(
        content=f"Deleted user {user_id}",
        status_code=status.HTTP_204_NO_CONTENT,
    )
