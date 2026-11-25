from typing import Annotated

from starlette.exceptions import HTTPException as StarletteHttpException
from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

import models
from database import Base, engine, get_db_session
from schemas import PostResponse, PostCreate, UserCreate, UserResponse, PostUpdate, UserUpdate

# Создание БД
Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="templates")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media", StaticFiles(directory="media"), name="media")


@app.get("/", include_in_schema=False, name="home")
@app.get("/posts", include_in_schema=False, name="posts")
def home_page(request: Request, db: Annotated[Session, Depends(get_db_session)]):
    result = db.execute(select(models.Post))
    posts = result.scalars().all()
    return templates.TemplateResponse(
        request,
        "home_page.html",
        context={"posts": posts, "title": "Посты"}
    )

@app.get("/posts/{post_id}", include_in_schema=False)
def get_post_detail_page(request: Request, post_id: int, db: Annotated[Session, Depends(get_db_session)]):
    result = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if post:
        context = {"title": post.title[:20], "post": post}
        return templates.TemplateResponse(
            request,
            "post_detail.html",
            context=context
        )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")


@app.get("/users/{user_id}/posts", include_in_schema=False, name="posts_by_user")
def user_posts_page(
        request: Request,
        user_id: int,
        db: Annotated[Session, Depends(get_db_session)]
):
    get_user_stmt = select(models.User).where(models.User.id == user_id)
    get_user_result = db.execute(get_user_stmt)
    user = get_user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    posts_stmt = select(models.Post).where(models.Post.user_id == user.id)
    posts_result = db.execute(posts_stmt)
    posts = posts_result.scalars().all()
    return templates.TemplateResponse(
        request,
        "user_posts.html",
        {"posts": posts, "title": f"Посты от {user.username}", "user": user}
    )


@app.post("/api/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Annotated[Session, Depends(get_db_session)]):
    username_exist_stmt = select(models.User).where(models.User.username == user.username)
    username_exists_result = db.execute(username_exist_stmt)
    existing_user = username_exists_result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )

    email_exists_stmt = select(models.User).where(models.User.email == user.email)
    email_exists_result = db.execute(email_exists_stmt)
    email_exists_user = email_exists_result.scalar_one_or_none()
    if email_exists_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    new_user = models.User(
        username=user.username,
        email=user.email
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.get("/api/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Annotated[Session, Depends(get_db_session)]):
    get_user_stmt = select(models.User).where(models.User.id == user_id)
    get_user_result = db.execute(get_user_stmt)
    user = get_user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@app.get("/api/users/{user_id}/posts", response_model=list[PostResponse], status_code=status.HTTP_200_OK)
def get_posts_by_user(user_id: int, db: Annotated[Session, Depends(get_db_session)]):
    get_user_stmt = select(models.User).where(models.User.id == user_id)
    get_user_result = db.execute(get_user_stmt)
    user = get_user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    posts_stmt = select(models.Post).where(models.Post.user_id == user.id)
    posts_result = db.execute(posts_stmt)
    posts = posts_result.scalars().all()
    return posts


@app.patch("/api/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_update_data: UserUpdate,
    db: Annotated[Session, Depends(get_db_session)]
):
    user_result = db.execute(select(models.User).where(models.User.id == user_id))
    user = user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    user_result = db.execute(select(models.User).where(models.User.username == user_update_data.username))
    user_with_name = user_result.scalar_one_or_none()
    if user_with_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    user_result = db.execute(select(models.User).where(models.User.email == user_update_data.email))
    user_with_email = user_result.scalar_one_or_none()
    if user_with_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    if user_update_data.username:
        user.username = user_update_data.username
    if user_update_data.email:
        user.email = user_update_data.email
    if user_update_data.image:
        user.image = user_update_data.image
    db.commit()
    db.refresh(user)
    return user

@app.delete("/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Annotated[Session, Depends(get_db_session)]):
    user_result = db.execute(select(models.User).where(models.User.id == user_id))
    user = user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    db.delete(user)
    db.commit()

@app.post(
    "/api/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED
)
def create_post(post_create: PostCreate, db:Annotated[Session, Depends(get_db_session)]):
    get_user_stmt = select(models.User).where(models.User.id == post_create.user_id)
    get_user_result = db.execute(get_user_stmt)
    user = get_user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    new_post = models.Post(
        title=post_create.title,
        content=post_create.content,
        user_id=post_create.user_id,
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post

@app.get("/api/posts", response_model=list[PostResponse])
def get_posts(db: Annotated[Session, Depends(get_db_session)]):
    result = db.execute(select(models.Post))
    posts = result.scalars().all()
    return posts

@app.get("/api/posts/{post_id}", response_model=PostResponse)
def get_post(post_id: int, db: Annotated[Session, Depends(get_db_session)]):
    post_stmt = select(models.Post).where(models.Post.id == post_id)
    post_result = db.execute(post_stmt)
    post = post_result.scalar_one_or_none()
    if post:
        return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

@app.patch("/api/posts/{post_id}", response_model=PostResponse)
def update_post_partial(
    post_id: int,
    post_update_data: PostUpdate,
    db: Annotated[Session, Depends(get_db_session)]
):
    post_stmt = select(models.Post).where(models.Post.id == post_id)
    post_result = db.execute(post_stmt)
    post = post_result.scalar_one_or_none()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    data_for_update = post_update_data.model_dump(exclude_unset=True)
    for field, value in data_for_update.items():
        setattr(post, field, value)

    db.commit()
    db.refresh(post)
    return post

@app.put("/api/posts/{post_id}", response_model=PostResponse)
def update_post_full(
    post_id: int,
    post_update_data: PostCreate,
    db: Annotated[Session, Depends(get_db_session)],
):
    post_stmt = select(models.Post).where(models.Post.id == post_id)
    post_result = db.execute(post_stmt)
    post = post_result.scalar_one_or_none()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    if post_update_data.user_id != post.user_id:
        user_result = db.execute(select(models.User).where(models.User.id == post_update_data.user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
    post.title = post_update_data.title
    post.content = post_update_data.content
    post.user_id = post_update_data.user_id

    db.commit()
    db.refresh(post)
    return post


@app.delete("/api/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, db: Annotated[Session, Depends(get_db_session)]):
    post_stmt = select(models.Post).where(models.Post.id == post_id)
    post_result = db.execute(post_stmt)
    post = post_result.scalar_one_or_none()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    db.delete(post)
    db.commit()

@app.exception_handler(StarletteHttpException)
def general_http_exception_handler(request: Request, exception: StarletteHttpException):
    message = exception.detail if exception.detail else "Что-то пошло не так. Повторите запрос."
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=exception.status_code,
            content={"detail": message}
        )
    return templates.TemplateResponse(
        request,
        "error.html",
        context={
            "error_message": message,
            "status_code": exception.status_code
        },
        status_code=exception.status_code
    )

@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exception: RequestValidationError):
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": exception.errors()}
        )
    return templates.TemplateResponse(
        request,
        "error.html",
        context={
            "error_message": "Что-то пошло не так. Повторите запрос.",
            "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT
        },
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT
    )
