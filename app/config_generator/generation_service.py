"""Сервис для координации синхронизации репозитория и генерации кода."""

from app.app_config import settings
from app.config_generator.core import get_generators
from app.config_generator.git_utils import (
    checkout_tracking_branch,
    get_current_commit_id,
    list_remote_branches,
    sync_repo,
    commit_and_push_current_branch,
)
from app.logger import get_logger
import shutil

logger = get_logger(__name__)


class GenerationError(Exception):
    """Вызывается при ошибке процесса генерации."""


def trigger_generation() -> None:
    """Синхронизирует репозиторий, запускает генерацию и коммитит в текущую ветку.

    Raises:
        GenerationError: Если любой этап процесса завершился с ошибкой
    """
    logger.info(f"Старт работы сервиса генерации конфигураций.")
    repo_path = None
    try:
        # Синхронизация репозитория
        repo_path = sync_repo(
            repo_url=settings.REPO_URL,
            branch=settings.REMOTE_REPO_BRANCH,
            dest_dir=settings.repo_root,
        )
        logger.info(f"Репозиторий готов в {repo_path}. Запуск генерации...")

        # Получаем список веток по маске 'candidate*'
        candidate_branches = list_remote_branches(repo_path, "candidate*")
        if not candidate_branches:
            logger.warning("Не найдено веток по маске 'candidate*'")

        errors: list[str] = []
        generators = get_generators()
        if not generators:
            logger.warning("Не найдено ни одного генератора в templates/*/generator.py")
        for branch in candidate_branches:
            try:
                logger.info(f"=== Обработка ветки {branch} ===")
                checkout_tracking_branch(repo_path, branch)

                # Получение ID коммита для текущей ветки
                commit_id = get_current_commit_id(repo_path)
                logger.info(f"Текущий ID коммита ({branch}): {commit_id}")

                # Запуск генерации всех зарегистрированных шаблонов
                for gen in generators:
                    try:
                        gen.generate_config()
                    except Exception as gen_exc:
                        raise RuntimeError(
                            f"Генератор {gen.__module__} завершился ошибкой: {gen_exc}"
                        )
                logger.info(f"Генерация успешно завершена для {branch}")

                # Коммитим изменения в текущую ветку и пушим без создания release_candidate
                commit_and_push_current_branch(
                    repo_path,
                    message=f"Auto-generated configs for branch {branch} (from {commit_id})",
                )
            except Exception as branch_exc:
                msg = f"Ошибка при обработке ветки {branch}: {branch_exc}"
                logger.error(msg)
                errors.append(msg)

        if errors:
            raise GenerationError("; ".join(errors))

    except Exception as exc:
        error_msg = f"Ошибка генерации: {exc}"
        logger.error(error_msg)
        raise GenerationError(error_msg) from exc
    finally:
        # После обработки вебхука очищаем локальный клон репозитория,
        # чтобы при следующем вызове всегда получать свежую копию
        try:
            if repo_path and repo_path.exists():
                shutil.rmtree(repo_path.as_posix(), ignore_errors=True)
                logger.info(f"Локальный репозиторий удалён: {repo_path}")
        except Exception as cleanup_exc:
            logger.warning(
                f"Не удалось удалить локальный репозиторий {repo_path}: {cleanup_exc}"
            )
        logger.info(f"Сервис генерации конфигураций завершил работу.")
        logger.info("=" * 100)
        
