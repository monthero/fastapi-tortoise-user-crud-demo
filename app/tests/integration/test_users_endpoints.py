import asyncio
from datetime import datetime
from secrets import token_hex
from typing import List
from uuid import uuid4

from faker import Faker
from fastapi.testclient import TestClient

from app.config import settings
from app.db.models import User
from app.schemas import DisplayUser
from app.utils import get_password_hash


Faker.seed(0)
faker: Faker = Faker()
user_ids: List[str] = []

BASE_URL: str = "/api/users"


def test_setup(event_loop: asyncio.AbstractEventLoop):
    for _ in range(10):
        user = event_loop.run_until_complete(
            User.create(
                username=f"user-{token_hex(5)}",
                first_name=faker.first_name(),
                last_name=faker.last_name(),
                password=get_password_hash("123123"),
                profile_image="https://www.dutchnews.nl/wpcms/wp-content/uploads/2017/01/Raccoon.jpg",  # noqa
            )
        )
        user_ids.append(str(user.id))


async def get_user_by_id(user_id: str):
    user = await User.get(id=user_id)
    return user


def test_create_user(client: TestClient):
    response = client.post(
        BASE_URL,
        json={
            "username": f"user-test",
            "firstName": faker.first_name(),
            "lastName": faker.last_name(),
            "password": "123123",
            "profileImage": "https://www.dutchnews.nl/wpcms/wp-content/uploads/2017/01/Raccoon.jpg",  # noqa
        },
    )

    assert response.status_code == 201
    assert response.headers["Content-Type"] == "application/json"
    data = response.json()
    assert all(
        field in data
        for field in DisplayUser.parse_obj(data).dict(by_alias=True).keys()
    )

    # Test that profile image was properly uploaded
    assert data["profileImage"].endswith(f'{data["id"]}.jpg')
    assert settings.UPLOAD_FOLDER.joinpath(
        "profile_images", *data["profileImage"].split("/")
    ).is_file()


def test_create_with_existing_username(client: TestClient):
    response = client.post(BASE_URL, json={
        "username": f"user-test",
        "firstName": faker.first_name(),
        "lastName": faker.last_name(),
        "password": "123123",
        "profileImage": "https://www.dutchnews.nl/wpcms/wp-content/uploads/2017/01/Raccoon.jpg",  # noqa
    })

    assert response.status_code == 409
    assert response.json()["detail"] == (
        f'The username "user-test" is already in use.'
    )


def test_list_users(client: TestClient, event_loop: asyncio.AbstractEventLoop):
    response = client.get(BASE_URL)

    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    data = response.json()

    assert isinstance(data, list)
    assert all(isinstance(item, dict) for item in data)

    for item in data:
        assert all(
            field in item
            for field in DisplayUser.parse_obj(item).dict(by_alias=True).keys()
        )

    user_ids.extend([item.get("id") for item in data])

    assert len(data) == event_loop.run_until_complete(
        User.exclude(deleted_at__isnull=False).count()
    )


def test_get_user(client: TestClient):
    for user_id in user_ids:
        response = client.get(f"{BASE_URL}/{user_id}")

        assert response.status_code == 200
        assert response.headers["Content-Type"] == "application/json"
        data = response.json()

        assert isinstance(data, dict)

        assert all(
            field in data
            for field in DisplayUser.parse_obj(data).dict(by_alias=True).keys()
        )


def test_delete_user(
    client: TestClient, event_loop: asyncio.AbstractEventLoop
):
    response = client.delete(f"{BASE_URL}/{user_ids[0]}")

    assert response.status_code == 204
    assert response.headers["Content-Type"] == "text/plain; charset=utf-8"
    assert response.text == f"Deleted user {user_ids[0]}"

    # testing that it has now a datetime value in the delete_at property
    user_obj = event_loop.run_until_complete(get_user_by_id(user_ids[0]))
    assert str(user_obj.id) == user_ids[0]
    assert isinstance(user_obj.deleted_at, datetime)

    response = client.get(f"/api/users/{user_ids[0]}")
    assert response.status_code == 404
    assert response.headers["Content-Type"] == "application/json"
    data = response.json()

    assert data["detail"] == f"User with id {user_ids[0]} has been deleted."


def test_get_user_not_found(client: TestClient):
    random_user_id: str = str(uuid4())
    response = client.get(f"{BASE_URL}/{random_user_id}")

    assert response.status_code == 404
    assert response.headers["Content-Type"] == "application/json"
    assert (
        response.json()["detail"]
        == f"User with id {random_user_id} was not found"
    )


def test_update_user(client: TestClient, event_loop: asyncio.AbstractEventLoop):
    first_name, last_name = faker.name().split(" ")

    response = client.put(f"{BASE_URL}/{user_ids[-1]}", json={
        "firstName": first_name,
        "lastName": last_name,
    })
    assert response.status_code == 200

    user_obj = event_loop.run_until_complete(get_user_by_id(user_ids[-1]))
    assert str(user_obj.id) == user_ids[-1]
    assert user_obj.first_name == first_name
    assert user_obj.last_name == last_name


def test_update_deleted_user(client: TestClient):
    first_name, last_name = faker.name().split(" ")
    response = client.put(f"{BASE_URL}/{user_ids[0]}", json={
        "firstName": first_name,
        "lastName": last_name,
    })

    assert response.status_code == 404
    assert response.json()["detail"] == (
        f'User with id {user_ids[0]} has been deleted.'
    )


def test_update_user_with_existing_username(client: TestClient):
    response = client.put(f"{BASE_URL}/{user_ids[-2]}", json={
        "username": "user-test",
    })

    assert response.status_code == 409
    assert response.json()["detail"] == (
        f'The username \"user-test\" is already in use.'
    )


def test_tear_down(event_loop: asyncio.AbstractEventLoop):
    for item in settings.UPLOAD_FOLDER.iterdir():
        if not item.is_file():
            continue

        if any(uid in item.name for uid in user_ids):
            item.unlink()

    event_loop.run_until_complete(
        User.filter(username__startswith="user-").all().delete()
    )

    assert (
        event_loop.run_until_complete(
            User.filter(username__startswith="user-").count()
        )
        == 0
    )
