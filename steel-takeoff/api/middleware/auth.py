"""
JWT Authentication Middleware
Simple token validation like .NET's [Authorize] attribute.

Your .NET CRM generates tokens, this API just validates them.
Use the same secret key in both applications.
"""

from datetime import datetime, timezone
from typing import Optional
import jwt
from jwt.exceptions import PyJWTError, ExpiredSignatureError, InvalidTokenError
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from api.config import settings


# HTTP Bearer scheme for swagger UI
security = HTTPBearer(
    scheme_name="JWT",
    description="Enter your JWT token from the CRM application",
    auto_error=False
)


class UserInfo:
    """Current user information from token"""
    def __init__(self, user_id: str, email: str = None, name: str = None, roles: list = None):
        self.user_id = user_id
        self.email = email
        self.name = name
        self.roles = roles or []


def validate_token(token: str) -> UserInfo:
    """
    Validate JWT token and return user info.
    Uses same secret key as your .NET CRM.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt.secret_key,
            algorithms=[settings.jwt.algorithm],
            options={"verify_exp": True}
        )
        
        # Extract user info - handle both .NET and standard formats
        user_id = (
            payload.get("sub") or 
            payload.get("nameid") or 
            payload.get("http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier")
        )
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: no user identifier"
            )
        
        email = (
            payload.get("email") or 
            payload.get("http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress")
        )
        
        name = (
            payload.get("name") or 
            payload.get("unique_name") or
            payload.get("http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name")
        )
        
        roles = payload.get("roles") or payload.get("role") or []
        if isinstance(roles, str):
            roles = [roles]
        
        return UserInfo(user_id=user_id, email=email, name=name, roles=roles)
        
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )
    except PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}"
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> UserInfo:
    """
    Dependency for protected routes - like .NET's [Authorize].
    
    Usage:
    ```python
    @router.post("/analyze")
    async def analyze(user: UserInfo = Depends(get_current_user)):
        # user is authenticated
        pass
    ```
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return validate_token(credentials.credentials)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[UserInfo]:
    """
    Dependency for optionally authenticated routes.
    Returns None if no token, user info if valid token.
    """
    if credentials is None:
        return None
    
    try:
        return validate_token(credentials.credentials)
    except HTTPException:
        return None


def require_roles(*required_roles: str):
    """
    Dependency factory to require specific roles - like .NET's [Authorize(Roles = "Admin")].
    
    Usage:
    ```python
    @router.post("/admin")
    async def admin_only(user: UserInfo = Depends(require_roles("admin"))):
        pass
    ```
    """
    async def role_checker(user: UserInfo = Depends(get_current_user)) -> UserInfo:
        for role in required_roles:
            if role in user.roles:
                return user
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required: {', '.join(required_roles)}"
        )
    
    return role_checker
