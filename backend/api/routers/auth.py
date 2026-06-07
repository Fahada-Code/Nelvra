from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_db
from ..exceptions import NelvraException
from ..schemas.auth import GitHubRegisterRequest, RegisterResponse, UserResponse
from ..services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


def _verify_internal_secret(x_internal_secret: str | None = Header(default=None)) -> None:
    """Verifies the shared secret between the Next.js frontend and this API."""
    if not settings.internal_secret:
        raise NelvraException(
            message="INTERNAL_SECRET is not configured on this server",
            code="SERVER_MISCONFIGURED",
            status_code=500,
        )
    if x_internal_secret != settings.internal_secret:
        raise NelvraException(
            message="Invalid internal secret",
            code="UNAUTHORIZED",
            status_code=401,
        )


@router.post("/register", response_model=RegisterResponse, status_code=200)
async def register_github_user(
    data: GitHubRegisterRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_verify_internal_secret),
) -> RegisterResponse:
    """
    Called by the Next.js frontend after GitHub OAuth completes.
    Creates the user + default project on first login.
    Returns the API key only on first login — the frontend must store it in the session.
    """
    user, project, plaintext_key = await UserService.register_or_login(db, data)

    existing_key_prefix = None
    if plaintext_key is None:
        from ..services.api_key_service import ApiKeyService

        keys = await ApiKeyService.list_for_project(db, project.id)
        if keys:
            existing_key_prefix = keys[0].key_prefix

    return RegisterResponse(
        user=UserResponse.model_validate(user),
        project_id=project.id,
        api_key=plaintext_key,
        existing_api_key_prefix=existing_key_prefix,
    )
