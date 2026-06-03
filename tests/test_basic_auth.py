from base64 import b64encode

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def auth_header(username: str = "user", password: str = "123qweASD") -> dict[str, str]:
    token = b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
    return {"Authorization": f"Basic {token}"}


def test_basic_auth_blocks_unauthorized_requests() -> None:
    response = client.get("/")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == 'Basic realm="shipment_planner"'


def test_basic_auth_allows_authorized_requests() -> None:
    response = client.get("/", headers=auth_header())
    assert response.status_code == 200


def test_basic_auth_rejects_wrong_password() -> None:
    response = client.get("/", headers=auth_header(password="wrong"))
    assert response.status_code == 401
