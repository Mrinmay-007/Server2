
# =========================================
# schemas.py
# =========================================

from pydantic import BaseModel
from typing import Optional   


class Login(BaseModel):
    username: str
    password: str


class TokenData(BaseModel):
    email: Optional[str] = None   


class Token(BaseModel):
    access_token: str
    token_type: str


class ResetPwRequest(BaseModel):
    old_pw: str
    new_pw: str