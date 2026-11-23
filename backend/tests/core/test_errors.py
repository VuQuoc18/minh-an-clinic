from fastapi import FastAPI, Query
from fastapi.testclient import TestClient
from pydantic import BaseModel, field_validator

from app.core.errors import VALIDATION_MESSAGE, AppError, register_error_handlers


class Body(BaseModel):
    name: str
    age: int

    @field_validator("name")
    @classmethod
    def _check_name(cls, value: str) -> str:
        if len(value) < 2:
            raise ValueError("Họ tên dài từ 2 ký tự.")
        return value


def _client() -> TestClient:
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/boom")
    def boom() -> None:
        raise AppError(409, "SOMETHING_TAKEN", "Đã có người dùng.")

    @app.post("/items")
    def create(body: Body) -> dict:
        return body.model_dump()

    @app.get("/search")
    def search(phone: str = Query(max_length=3)) -> dict:
        return {"phone": phone}

    return TestClient(app)


def test_app_error_returns_code_and_message():
    response = _client().get("/boom")

    assert response.status_code == 409
    assert response.json() == {
        "detail": {"code": "SOMETHING_TAKEN", "message": "Đã có người dùng."}
    }


def test_single_validation_error_uses_validator_message_without_pydantic_prefix():
    response = _client().post("/items", json={"name": "A", "age": 1})

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "VALIDATION_ERROR"
    assert detail["message"] == "Họ tên dài từ 2 ký tự."
    assert detail["errors"] == [{"field": "name", "message": "Họ tên dài từ 2 ký tự."}]


def test_several_validation_errors_use_generic_message_and_list_each_field():
    response = _client().post("/items", json={"name": "A", "age": "x"})

    detail = response.json()["detail"]
    assert detail["message"] == VALIDATION_MESSAGE
    assert {e["field"] for e in detail["errors"]} == {"name", "age"}


def test_query_validation_error_names_the_parameter():
    response = _client().get("/search", params={"phone": "12345"})

    assert response.status_code == 422
    assert response.json()["detail"]["errors"][0]["field"] == "phone"
