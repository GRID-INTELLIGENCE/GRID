from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    username: str
    email: str
    full_name: str | None = None
    is_active: bool = True
    trust_tier: str = "user"  # anon, user, verified, privileged


class UserCreate(UserBase):
    password: str


class UserUpdate(UserBase):
    password: str | None = None


class User(UserBase):
    id: int
    created_at: datetime
    last_login: datetime | None = None
    login_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None
