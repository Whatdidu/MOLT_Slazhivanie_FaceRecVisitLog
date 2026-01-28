"""
Роутер для интерактивной презентации проекта.
Доступен без авторизации.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/showcase", tags=["Showcase"])

templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def showcase_index(request: Request):
    """Главная страница презентации."""
    return templates.TemplateResponse(
        "showcase/index.html",
        {"request": request}
    )


@router.get("/cabinet/", response_class=HTMLResponse)
async def showcase_cabinet(request: Request):
    """Страница кабинета с доступом к системе."""
    return templates.TemplateResponse(
        "showcase/cabinet.html",
        {"request": request}
    )
