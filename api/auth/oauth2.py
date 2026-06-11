
# =========================================
# oauth2.py
# =========================================

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from api.auth import auth_token



oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="user/login"
)

async def get_current_user(
    data: str = Depends(oauth2_scheme)
):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    return await auth_token.verify_token(
        data,
        credentials_exception
    )