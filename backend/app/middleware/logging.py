import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log request execution details, client information, and processing time."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        client_host = request.client.host if request.client else "unknown"

        try:
            response = await call_next(request)
            duration = time.time() - start_time
            duration_str = f"{duration:.4f}s"

            # Log request details
            logger.info(
                f"{client_host} - {request.method} {request.url.path} - Status: {response.status_code} - Duration: {duration_str}"
            )

            # Inject processing time header
            response.headers["X-Process-Time"] = duration_str

            return response

        except Exception as exc:
            duration = time.time() - start_time
            duration_str = f"{duration:.4f}s"

            # Log unhandled/failed request details
            logger.error(
                f"{client_host} - {request.method} {request.url.path} - Failed - Duration: {duration_str} - Error: {str(exc)}"
            )
            raise exc
