import hmac
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from app.config import settings

# API Key header scheme reading 'X-API-Key' from request headers
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str | None = Depends(api_key_header)) -> str:
    """Verify that the request provides a valid X-API-Key header in constant time.

    Raises:
        HTTPException 401 Unauthorized if key is missing or invalid.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Constant-time string comparison to prevent timing attacks
    if not hmac.compare_digest(api_key.encode("utf-8"), settings.admin_api_key.encode("utf-8")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return api_key
