from pydantic import BaseModel


class UserCreate(BaseModel):
    display_name: str
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    display_name: str
    username: str
    level: int
    xp: int
    streak: int
    skill_rating: int

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    user: UserResponse
