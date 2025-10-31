"""Утилиты для валидации payload webhook запросов."""

from typing import Optional

from app.app_config import settings


def is_git_event(x_gitlab_event: Optional[str], x_github_event: Optional[str]) -> bool:
    """Проверяет, является ли запрос от Git сервиса (GitLab или GitHub).

    Args:
        x_gitlab_event: Значение заголовка X-Gitlab-Event
        x_github_event: Значение заголовка X-GitHub-Event

    Returns:
        True если хотя бы один заголовок присутствует, False иначе
    """
    return bool(x_gitlab_event or x_github_event)


def extract_ref(payload: Optional[dict]) -> Optional[str]:
    """Извлекает git ref из payload webhook запроса.

    Args:
        payload: Словарь с данными webhook запроса

    Returns:
        Строка ref (например, 'refs/heads/develop') или None
    """
    if isinstance(payload, dict):
        return payload.get("ref")
    return None


def is_allowed_branch(ref: Optional[str]) -> bool:
    """Проверяет, соответствует ли ref из webhook разрешённой ветке.

    Args:
        ref: Git ref из webhook (например, 'refs/heads/develop')

    Returns:
        True если ref совпадает с веткой по умолчанию, False иначе
    """
    if not ref:
        return False

    default_branch = settings.REMOTE_REPO_BRANCH
    return ref in (f"refs/heads/{default_branch}", default_branch)
