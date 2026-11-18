from starlette.exceptions import HTTPException as StarletteHttpException
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

templates = Jinja2Templates(directory="templates")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

posts: list[dict] = [
    {
        "id": 1,
        "author": "Programmer",
        "title": "Асинхронность: когда await становится образом жизни",
        "content": "Проснулся, сделал await coffee(), потом await shower(), потом await commute(). К обеду понял, что забыл await breakfast() и теперь живу в состоянии pending.",
        "created_at": "October 15, 2026"
    },
    {
        "id": 2,
        "author": "Programmer",
        "title": "Тесты, которых не существует",
        "content": "Написал 47 тестов. 46 зелёных. Один красный. Тот самый, который проверяет, что пользователь не может удалить себя дважды. Классика.",
        "created_at": "October 18, 2026",
    },
    {
        "id": 3,
        "author": "Bobik-dog",
        "title": "Почему я лаю на пылесос",
        "content": "Он рычит. Он двигается. Он опасен. Я защищаю дом. Не благодарите.",
        "created_at": "November 11, 2026",
    },
]

def get_post_by_id(post_id: int):
    for post in posts:
        if post["id"] == post_id:
            return post
    return None

@app.get("/", include_in_schema=False, name="home")
@app.get("/posts", include_in_schema=False, name="posts")
def home_page(request: Request):
    return templates.TemplateResponse(
        request,
        "home_page.html",
        context={"posts": posts, "title": "Посты"}
    )

@app.get("/posts/{post_id}")
def get_post_detail_page(request: Request, post_id: int):
    post = get_post_by_id(post_id)
    if post:
        context = {"title": post.get("title")[:20], "post": post}
        return templates.TemplateResponse(
            request,
            "post_detail.html",
            context=context
        )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

@app.get("/api/posts")
def get_posts():
    return posts

@app.get("/api/posts/{post_id}")
def get_post(post_id: int):
    post = get_post_by_id(post_id)
    if post:
        return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

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
