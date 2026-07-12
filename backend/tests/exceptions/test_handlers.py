from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from app.exceptions.handlers import register_exception_handlers
from app.shared.validation import ValidationError
from pydantic import BaseModel

app = FastAPI()
register_exception_handlers(app)


class DummyModel(BaseModel):
    name: str
    age: int


@app.post("/test-validation")
def trigger_validation(data: DummyModel):
    return {"status": "ok"}


@app.get("/test-custom-validation")
def trigger_custom_validation():
    raise ValidationError(
        field="email", message="Invalid email domain.", status_code=400
    )


@app.get("/test-http-exception")
def trigger_http_exception():
    raise HTTPException(status_code=404, detail="Resource could not be found.")


@app.get("/test-unhandled-exception")
def trigger_unhandled():
    raise ValueError("Something unexpected broke.")


client = TestClient(app, raise_server_exceptions=False)


def test_request_validation_error_handler():
    response = client.post(
        "/test-validation", json={"name": "Alice", "age": "not-a-number"}
    )
    assert response.status_code == 422
    json_data = response.json()
    assert json_data["success"] is False
    assert json_data["error"]["code"] == "VALIDATION_ERROR"
    assert "body -> age" in json_data["error"]["message"]


def test_custom_validation_error_handler():
    response = client.get("/test-custom-validation")
    assert response.status_code == 400
    json_data = response.json()
    assert json_data["success"] is False
    assert json_data["error"]["code"] == "VALIDATION_ERROR"
    assert json_data["error"]["message"] == "email: Invalid email domain."


def test_http_exception_handler():
    response = client.get("/test-http-exception")
    assert response.status_code == 404
    json_data = response.json()
    assert json_data["success"] is False
    assert json_data["error"]["code"] == "NOT_FOUND"
    assert json_data["error"]["message"] == "Resource could not be found."


def test_unhandled_exception_handler():
    response = client.get("/test-unhandled-exception")
    assert response.status_code == 500
    json_data = response.json()
    assert json_data["success"] is False
    assert json_data["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert json_data["error"]["message"] == "An unexpected error occurred."
