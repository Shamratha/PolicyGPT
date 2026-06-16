import jwt
from jwt.algorithms import RSAAlgorithm
import httpx
import logging
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)

# Local JWKs cache to prevent hitting Clerk servers on every single API request
_jwks_cache: Optional[Dict[str, Any]] = None

def get_jwks() -> Optional[Dict[str, Any]]:
    global _jwks_cache
    if _jwks_cache:
        return _jwks_cache

    if not settings.CLERK_JWKS_URL:
        return None

    try:
        response = httpx.get(settings.CLERK_JWKS_URL, timeout=5.0)
        response.raise_for_status()
        _jwks_cache = response.json()
        return _jwks_cache
    except Exception as e:
        logger.error(f"Failed to fetch JWKs from Clerk URL: {e}")
        return None

def verify_clerk_token(token: str) -> Dict[str, Any]:
    """
    Decodes and validates a Clerk JWT.
    Provides a development bypass if CLERK_JWKS_URL is empty or key is mock.
    """
    try:
        # Development mode check
        if not settings.CLERK_JWKS_URL or settings.ENVIRONMENT == "development" or settings.OPENAI_API_KEY.startswith("sk-mock"):
            # Decode token without verification for ease of development & offline mode
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload

        jwks = get_jwks()
        if not jwks:
            raise HTTPException(status_code=500, detail="Clerk public key set is unavailable.")

        # Extract kid from jwt header
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        if not kid:
            raise HTTPException(status_code=401, detail="Invalid token header (missing kid).")

        # Find matching key in JWKs
        public_key: Any = None
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                public_key = RSAAlgorithm.from_jwk(key)
                break

        if not public_key:
            raise HTTPException(status_code=401, detail="JWK key ID not found in signature sets.")

        # Verify token signature and claims
        # Clerk issuer format is usually https://clerk.your-domain.com or https://your-app.clerk.accounts.dev
        payload = jwt.decode(
            token,
            public_key,
            algorithms=[settings.JWT_ALGORITHM or "RS256"],
            options={"verify_aud": False} # Skip audience check if client-specific setup varies
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Authentication token has expired.")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid authentication token: {str(e)}")
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(status_code=401, detail="Could not validate credentials.")

def get_current_user_claims(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict[str, Any]:
    """
    Dependency injection for FastAPI routes. Extract claims or raise 401.
    """
    if not credentials:
        # For development ease, if no token is passed, return a mock user payload
        if settings.ENVIRONMENT == "development" or settings.OPENAI_API_KEY.startswith("sk-mock"):
            return {
                "sub": "mock_clerk_id_12345",
                "email": "dev-user@policygpt.ai"
            }
        raise HTTPException(status_code=401, detail="Authorization credentials missing.")
        
    token = credentials.credentials
    return verify_clerk_token(token)
