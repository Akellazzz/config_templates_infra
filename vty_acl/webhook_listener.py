"""FastAPI webhook endpoint для запуска генерации кода."""
from typing import Optional

from fastapi import FastAPI, Header, BackgroundTasks
from fastapi.responses import PlainTextResponse

from generation_service import trigger_generation
from webhook_validator import (
    extract_ref,
    is_allowed_branch,
    is_git_event,
)


app = FastAPI()


@app.post("/webhook", response_class=PlainTextResponse)
async def webhook(
    background_tasks: BackgroundTasks,
    payload: Optional[dict] = None,
    x_gitlab_event: Optional[str] = Header(default=None, alias="X-Gitlab-Event"),
    x_github_event: Optional[str] = Header(default=None, alias="X-GitHub-Event"),
):
    """Обрабатывает webhook запросы от GitLab/GitHub.
    
    Проверяет что:
    - Запрос от Git сервиса (имеет заголовок X-Gitlab-Event или X-GitHub-Event)
    - Запрос для настроенной ветки по умолчанию
    
    Если всё валидно, запускает генерацию в фоновом режиме.
    """
    # Проверка что запрос от Git сервиса
    if not is_git_event(x_gitlab_event, x_github_event):
        return PlainTextResponse("Игнорируется\n", status_code=202)
    
    # Извлечение и валидация ветки
    ref = extract_ref(payload)
    if not is_allowed_branch(ref):
        return PlainTextResponse(f"Ветка {ref} игнорируется\n", status_code=202)
    
    # Запуск генерации в фоне
    background_tasks.add_task(trigger_generation)
    return PlainTextResponse("OK\n", status_code=200)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("webhook_listener:app", host="0.0.0.0", port=8080, reload=True)

"""
curl -X POST http://localhost:8080/webhook \
  -H 'Content-Type: application/json' \
  -H 'X-Gitlab-Event: Push Hook' \
  -d '{"ref":"refs/heads/main"}'
"""
