import httpx
from jose import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, HTTPBasic
from fastapi.security.utils import get_authorization_scheme_param
from fastapi import Request
from app.core.config import get_settings

settings = get_settings()
security = HTTPBearer(auto_error=False)  # auto_error=False lets us handle it manually

COGNITO_KEYS_URL = (
    f"https://cognito-idp.{settings.COGNITO_REGION}.amazonaws.com/"
    f"{settings.COGNITO_USER_POOL_ID}/.well-known/jwks.json"
)

_cached_keys = None

DEV_USER_PAYLOAD = {
    "sub": "dev-user-001",
    "email": "dev@smartcampus.local",
    "name": "Dev User",
}


async def get_cognito_public_keys():
    global _cached_keys
    if _cached_keys:
        return _cached_keys
    async with httpx.AsyncClient() as client:
        response = await client.get(COGNITO_KEYS_URL)
        _cached_keys = response.json()["keys"]
    return _cached_keys


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
):
    # ── DEV MODE: skip Cognito entirely ──────────────────────────────
    if settings.DEV_MODE:
        return DEV_USER_PAYLOAD

    # ── PRODUCTION: verify Cognito JWT ───────────────────────────────
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = credentials.credentials
    try:
        headers = jwt.get_unverified_headers(token)
        kid = headers["kid"]

        keys = await get_cognito_public_keys()
        public_key = next((k for k in keys if k["kid"] == kid), None)
        if not public_key:
            raise HTTPException(status_code=401, detail="Public key not found")

        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=settings.COGNITO_CLIENT_ID,
        )
        return payload

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token invalid: {str(e)}")


def get_current_user_id(payload: dict) -> str:
    return payload.get("sub", "")