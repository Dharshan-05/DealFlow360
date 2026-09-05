from fastapi import APIRouter
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.errors import ApplicationError
from app.main import app

# Create a mock router to verify exception handling scenarios
mock_router = APIRouter(prefix="/api/test-errors", tags=["Testing"])


class SamplePayload(BaseModel):
    required_field: str
    count: int


@mock_router.post("/validation")
async def validation_test(payload: SamplePayload):
    return {"received": payload.required_field}


@mock_router.get("/application-error")
async def application_error_test():
    raise ApplicationError(
        message="A custom domain error occurred",
        code="TEST_DOMAIN_ERROR",
        status_code=400,
        details={"field": "test_param"},
    )


@mock_router.get("/unhandled-error")
async def unhandled_error_test():
    raise RuntimeError("Unexpected internal crash with sensitive details: db_secret_123")


# Include mock router for test execution
app.include_router(mock_router)

client = TestClient(app, raise_server_exceptions=False)


def test_404_not_found_error():
    """Verify 404 returns structured error response."""
    response = client.get("/api/v1/non-existent-endpoint")
    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "NOT_FOUND"
    assert "Not Found" in body["error"]["message"]


def test_422_validation_error():
    """Verify RequestValidationError returns 422 with structured format."""
    response = client.post("/api/test-errors/validation", json={"count": "invalid_number"})
    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "Invalid request parameters" in body["error"]["message"]
    assert isinstance(body["error"]["details"], list)


def test_application_error():
    """Verify custom ApplicationError returns expected status and code."""
    response = client.get("/api/test-errors/application-error")
    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "TEST_DOMAIN_ERROR"
    assert body["error"]["message"] == "A custom domain error occurred"
    assert body["error"]["details"] == {"field": "test_param"}


def test_500_unhandled_exception_sanitized():
    """Verify unhandled 500 error sanitizes message and hides internal details."""
    response = client.get("/api/test-errors/unhandled-error")
    assert response.status_code == 500
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert body["error"]["message"] == "An internal server error occurred."
    # Ensure sensitive crash details are NEVER leaked to client
    assert "db_secret_123" not in str(body)
    assert "RuntimeError" not in str(body)
    assert "traceback" not in str(body).lower()
