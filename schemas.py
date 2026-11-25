from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, EmailStr


class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=120)
    email: EmailStr = Field(max_length=120)


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image: str | None
    path_to_image: str


class UserUpdate(BaseModel):
    username: str | None = Field(min_length=3, max_length=120, default=None)
    email: EmailStr | None = Field(max_length=120, default=None)
    image: str | None = Field(min_length=3, max_length=120, default=None)


class PostBase(BaseModel):
    title: str = Field(min_length=3, max_length=100)
    content: str = Field(min_length=1)


class PostUpdate(PostBase):
    title: str | None = Field(min_length=3, max_length=100, default=None)
    content: str | None = Field(min_length=1, default=None)


class PostCreate(PostBase):
    user_id: int # ВРЕМЕННО


class PostResponse(PostBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    author: UserResponse
    created_at: datetime
