
# =========================================
# token.py
# =========================================

from datetime import datetime, timedelta, timezone
import os
from jose import JWTError, jwt #type: ignore
import schemas
from dotenv import load_dotenv

load_dotenv()


SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

expire = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
ACCESS_TOKEN_EXPIRE_MINUTES = int(expire) if expire else 30



async def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None
):

    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY, #type: ignore
        algorithm=ALGORITHM #type: ignore
    )

    return encoded_jwt


async def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY, #type: ignore
            algorithms=[ALGORITHM] #type: ignore
        )

        email: str = payload.get("sub")   #type: ignore

        if email is None:
            raise credentials_exception

        token_data = schemas.TokenData(email=email)

        return token_data   

    except JWTError:
        raise credentials_exception