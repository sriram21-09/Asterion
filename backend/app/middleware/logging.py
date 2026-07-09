import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Configure a fallback logger if not configured elsewhere
logger = logging.getLogger("asterion")
if not logger.handlers:
    # Ensure stdout output for development/Docker environment
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log request execution details and processing time."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        duration = time.time() - start_time
        
        # Format duration to string
        duration_str = f"{duration:.4f}s"
        
        # Log request details
        logger.info(
            f"{request.method} {request.url.path} - Status: {response.status_code} - Duration: {duration_str}"
        )
        
        # Inject processing time header
        response.headers["X-Process-Time"] = duration_str
        
        return response
