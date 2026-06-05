from fastapi import Request
from fastapi.responses import JSONResponse


class NelvraException(Exception):
    """Base exception for all Nelvra API errors."""

    def __init__(self, message: str, code: str, status_code: int = 400):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


async def nelvra_exception_handler(request: Request, exc: NelvraException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "docs": f"https://docs.nelvra.io/errors/{exc.code}",
            }
        },
    )
