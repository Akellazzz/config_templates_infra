"""Сервис для координации синхронизации репозитория и генерации кода."""
from pathlib import Path

from app_config import settings
from generator import main as vty_acl_generator
from git_utils import (
    create_release_candidate_branch,
    get_current_commit_id,
    sync_repo,
)
import shutil


class GenerationError(Exception):
    """Вызывается при ошибке процесса генерации."""


def trigger_generation() -> None:
    """Синхронизирует репозиторий, запускает генерацию и создаёт ветку release candidate.
    
    Это основная функция оркестрации, которая:
    1. Синхронизирует репозиторий с удалённого сервера
    2. Запускает генератор vty_acl
    3. Создаёт и отправляет ветку release candidate с результатами
    
    Raises:
        GenerationError: Если любой этап процесса завершился с ошибкой
    """
    repo_path = None
    try:
        # Синхронизация репозитория
        repo_path = sync_repo(
            repo_url=settings.REPO_URL,
            branch=settings.REPO_DEFAULT_BRANCH,
            dest_dir=settings.repo_root,
        )
        print(f"Репозиторий готов в {repo_path}. Запуск генерации...")
        
        # Получение ID коммита перед генерацией
        commit_id = get_current_commit_id(repo_path)
        print(f"Текущий ID коммита: {commit_id}")
        
        # Запуск генерации
        vty_acl_generator()
        print("Генерация успешно завершена")
        
        # Создание ветки release candidate с результатами генерации
        create_release_candidate_branch(repo_path, commit_id)
        
    except Exception as exc:
        error_msg = f"Ошибка генерации: {exc}"
        print(error_msg)
        raise GenerationError(error_msg) from exc
    finally:
        # После обработки вебхука очищаем локальный клон репозитория,
        # чтобы при следующем вызове всегда получать свежую копию
        try:
            if repo_path and repo_path.exists():
                shutil.rmtree(repo_path.as_posix(), ignore_errors=True)
                print(f"Локальный репозиторий удалён: {repo_path}")
        except Exception as cleanup_exc:
            print(f"Не удалось удалить локальный репозиторий {repo_path}: {cleanup_exc}")

