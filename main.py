from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

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

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
@app.get("/posts", response_class=HTMLResponse, include_in_schema=False)
def home_page():
    post_content = posts[1]["content"]
    return HTMLResponse(
        content=f"<h1>{post_content}</h1>"
    )

@app.get("/api/posts")
def get_posts():
    return posts