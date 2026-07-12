from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.shared.validation import ValidationError
from app.core.logging import logger
from app.schemas.response import APIResponse, ErrorDetail

def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers for the FastAPI application."""

    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(request: Request, exc: RequestValidationError):
        errors = []
        for err in exc.errors():
            loc = " -> ".join(str(l) for l in err.get("loc", []))
            msg = err.get("msg", "Unknown error")
            errors.append(f"{loc}: {msg}")
        
        message = "; ".join(errors)
        response_body = APIResponse(
            success=False,
            error=ErrorDetail(code="VALIDATION_ERROR", message=message),
            detail=message
        )
        return JSONResponse(
            status_code=422,
            content=response_body.model_dump()
        )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError):
        message = f"{exc.field}: {exc.message}"
        response_body = APIResponse(
            success=False,
            error=ErrorDetail(code="VALIDATION_ERROR", message=message),
            detail=message
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=response_body.model_dump()
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        # Determine code based on status
        if exc.status_code == 404:
            code = "NOT_FOUND"
        elif exc.status_code == 401:
            code = "UNAUTHORIZED"
        elif exc.status_code == 403:
            code = "FORBIDDEN"
        elif exc.status_code == 400:
            code = "BAD_REQUEST"
        else:
            code = "HTTP_ERROR"
            
        # Parse detail message
        message = exc.detail
        if isinstance(exc.detail, dict):
            if "message" in exc.detail:
                message = exc.detail["message"]
            elif "detail" in exc.detail:
                message = exc.detail["detail"]
                
        response_body = APIResponse(
            success=False,
            error=ErrorDetail(code=code, message=str(message)),
            detail=str(message)
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=response_body.model_dump()
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled exception occurred: {str(exc)}")
        response_body = APIResponse(
            success=False,
            error=ErrorDetail(code="INTERNAL_SERVER_ERROR", message="An unexpected error occurred."),
            detail="An unexpected error occurred."
        )
        return JSONResponse(
            status_code=500,
            content=response_body.model_dump()
        )
