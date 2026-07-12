from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.logging import LoggingMiddleware
from app.core.config import settings
from unittest import mock

# Create a test app for isolating middleware behavior
app = FastAPI()
app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/ok")
def get_ok():
    return {"status": "ok"}

@app.get("/error")
def get_error():
    raise ValueError("Error in route")

client = TestClient(app)

def test_logging_middleware_success():
    with mock.patch("app.middleware.logging.logger") as mock_logger:
        response = client.get("/ok")
        assert response.status_code == 200
        assert "X-Process-Time" in response.headers
        mock_logger.info.assert_called_once()
        log_msg = mock_logger.info.call_args[0][0]
        assert "GET /ok - Status: 200" in log_msg

def test_logging_middleware_failure():
    with mock.patch("app.middleware.logging.logger") as mock_logger:
        try:
            client.get("/error")
        except ValueError:
            pass
        mock_logger.error.assert_called_once()
        log_msg = mock_logger.error.call_args[0][0]
        assert "GET /error - Failed" in log_msg

def test_cors_middleware_headers():
    response = client.get("/ok", headers={"Origin": "http://localhost:3000"})
    # Since allow_origins is "*", CORSMiddleware will reflect the request origin
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
