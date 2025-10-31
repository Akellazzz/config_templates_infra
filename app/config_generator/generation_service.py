"""Сервис для координации синхронизации репозитория и генерации кода."""

from app.app_config import settings
import importlib
from pathlib import Path
from app.config_generator.git_utils import (
    checkout_tracking_branch,
    get_current_commit_id,
    list_remote_branches,
    sync_repo,
    commit_and_push_current_branch,
)
import shutil


class GenerationError(Exception):
    """Вызывается при ошибке процесса генерации."""


def _discover_template_generators() -> list:
    """Находит callable генераторы из templates/*/generator.py (generate_config)."""
    generators: list = []
    base_pkg = "app.config_generator.templates"
    base_dir = Path(__file__).resolve().parent / "templates"
    if not base_dir.exists():
        return generators

    for entry in sorted(base_dir.iterdir()):
        if not entry.is_dir() or entry.name.startswith("_"):
            continue
        module_name = f"{base_pkg}.{entry.name}.generator"
        try:
            mod = importlib.import_module(module_name)
        except Exception as exc:
            print(f"Пропуск {module_name}: импорт неудачен ({exc})")
            continue

        gen = getattr(mod, "generate_config", None)
        if callable(gen):
            generators.append(gen)
        else:
            print(f"Пропуск {module_name}: нет функции generate_config()")

    return generators

def trigger_generation() -> None:
    """Синхронизирует репозиторий, запускает генерацию и коммитит в текущую ветку.

    Это основная функция оркестрации, которая:
    1. Синхронизирует репозиторий с удалённого сервера
    2. Запускает генератор vty_acl
    3. Коммитит и пушит изменения в ту же ветку candidate*

    Raises:
        GenerationError: Если любой этап процесса завершился с ошибкой
    """
    repo_path = None
    try:
        # Синхронизация репозитория
        repo_path = sync_repo(
            repo_url=settings.REPO_URL,
            branch=settings.REMOTE_REPO_BRANCH,
            dest_dir=settings.repo_root,
        )
        print(f"Репозиторий готов в {repo_path}. Запуск генерации...")

        # Получаем список веток по маске 'candidate*'
        candidate_branches = list_remote_branches(repo_path, "candidate*")
        if not candidate_branches:
            print("Не найдено веток по маске 'candidate*'")

        errors: list[str] = []
        template_generators = _discover_template_generators()
        if not template_generators:
            print("Не найдено ни одного генератора в templates/*/generator.py")
        for branch in candidate_branches:
            try:
                print(f"\n=== Обработка ветки {branch} ===")
                checkout_tracking_branch(repo_path, branch)

                # Получение ID коммита для текущей ветки
                commit_id = get_current_commit_id(repo_path)
                print(f"Текущий ID коммита ({branch}): {commit_id}")

                # Запуск генерации всех зарегистрированных шаблонов
                for gen in template_generators:
                    try:
                        gen()
                    except Exception as gen_exc:
                        raise RuntimeError(
                            f"Генератор {gen.__module__} завершился ошибкой: {gen_exc}"
                        )
                print(f"Генерация успешно завершена для {branch}")

                # Коммитим изменения в текущую ветку и пушим без создания release_candidate
                commit_and_push_current_branch(
                    repo_path,
                    message=f"Auto-generate configs for {branch} (from {commit_id})",
                )
            except Exception as branch_exc:
                msg = f"Ошибка при обработке ветки {branch}: {branch_exc}"
                print(msg)
                errors.append(msg)

        if errors:
            raise GenerationError("; ".join(errors))

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
            print(
                f"Не удалось удалить локальный репозиторий {repo_path}: {cleanup_exc}"
            )
