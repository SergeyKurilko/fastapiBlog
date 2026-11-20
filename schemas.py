from pydantic import BaseModel, Field, ConfigDict


class PostBase(BaseModel):
    title: str = Field(min_length=3, max_length=100)
    content: str = Field(min_length=1)
    author: str = Field(min_length=3, max_length=70)


class PostCreate(PostBase):
    pass


class PostResponse(PostBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: str
