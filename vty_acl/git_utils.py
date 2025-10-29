"""Утилиты для работы с Git репозиториями."""
import subprocess
from pathlib import Path


class GitError(Exception):
    """Вызывается при ошибке выполнения git операции."""


def run_git_command(args: list[str], repo_path: Path | None = None) -> str:
    """Выполняет git команду и возвращает её вывод.
    
    Args:
        args: Аргументы git команды (например, ['git', 'status'] или ['checkout', 'main'])
        repo_path: Опциональный путь к репозиторию. Если указан, используется 'git -C <repo_path>'
    
    Returns:
        Стандартный вывод команды в виде строки
    
    Raises:
        GitError: Если команда завершилась с ошибкой
    """
    git_args = ["git"]
    if repo_path:
        git_args.extend(["-C", repo_path.as_posix()])
    git_args.extend(args)
    
    result = subprocess.run(
        git_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    
    if result.returncode != 0:
        raise GitError(f"Ошибка выполнения git команды: {' '.join(git_args)}\n{result.stdout}")
    
    return result.stdout.strip()


def get_current_commit_id(repo_path: Path, short: bool = True) -> str:
    """Получает ID коммита из текущего HEAD.
    
    Args:
        repo_path: Путь к репозиторию
        short: Если True, возвращает короткий ID коммита (по умолчанию)
    
    Returns:
        ID коммита в виде строки
    """
    args = ["rev-parse", "--short", "HEAD"] if short else ["rev-parse", "HEAD"]
    return run_git_command(args, repo_path)


def list_remote_branches(repo_path: Path, pattern: str) -> list[str]:
    """Возвращает список удалённых веток origin, соответствующих шаблону.

    Args:
        repo_path: Путь к локальному клону репозитория
        pattern: Шаблон для фильтрации веток, например 'candidate*'

    Returns:
        Список имён веток без префикса 'origin/'
    """
    output = run_git_command(["branch", "-r", "--list", f"origin/{pattern}"], repo_path)
    branches: list[str] = []
    for line in output.splitlines():
        name = line.strip()
        if not name:
            continue
        if name.startswith("origin/"):
            name = name[len("origin/"):]
        branches.append(name)
    return branches


def checkout_tracking_branch(repo_path: Path, branch: str) -> None:
    """Переключается на локальную ветку, отслеживающую origin/<branch>.

    Создаёт/обновляет локальную ветку командой 'git checkout -B <branch> origin/<branch>'.
    """
    run_git_command(["checkout", "-B", branch, f"origin/{branch}"], repo_path)


def sync_repo(
    repo_url: str,
    branch: str,
    dest_dir: Path,
) -> Path:
    """Синхронизирует или клонирует git репозиторий.
    
    Args:
        repo_url: URL удалённого репозитория
        branch: Имя ветки для checkout
        dest_dir: Локальный путь к директории репозитория
    
    Returns:
        Путь к синхронизированному репозиторию
    """
    dest_path = Path(dest_dir)
    
    if (dest_path / ".git").exists():
        print(f"Синхронизация существующего репозитория в {dest_path}...")
        # Забираем все ветки и теги
        run_git_command(["fetch", "--all", "--prune"], dest_path)
        run_git_command(["checkout", branch], dest_path)
        run_git_command(["reset", "--hard", f"origin/{branch}"], dest_path)
    else:
        if not dest_path.exists():
            dest_path.mkdir(parents=True, exist_ok=True)
        
        print(f"Клонирование {repo_url} (ветка {branch}) в {dest_path}...")
        # Клонируем репозиторий с полной историей и всеми ветками
        run_git_command(["clone", "--branch", branch, repo_url, dest_path.as_posix()])
        # Сразу обновляем все ссылки и ветки
        run_git_command(["fetch", "--all", "--prune"], dest_path)
    
    return dest_path


def has_changes(repo_path: Path) -> bool:
    """Проверяет наличие изменений в рабочем дереве репозитория.
    
    Использует `git status --porcelain`, который выводит список модификаций в стабильном формате.
    Пустой вывод означает отсутствие изменений.
    
    Args:
        repo_path: Путь к репозиторию
    
    Returns:
        True если есть изменения, False иначе
    """
    status = run_git_command(["status", "--porcelain"], repo_path)
    return bool(status.strip())


def create_branch(repo_path: Path, branch_name: str) -> None:
    """Создаёт и переключается на новую ветку.
    
    Args:
        repo_path: Путь к репозиторию
        branch_name: Имя создаваемой ветки
    """
    run_git_command(["checkout", "-b", branch_name], repo_path)


def commit_all_changes(repo_path: Path, message: str) -> None:
    """Добавляет в staging и коммитит все изменения в репозитории.
    
    Args:
        repo_path: Путь к репозиторию
        message: Сообщение коммита
    """
    run_git_command(["add", "-A"], repo_path)
    run_git_command(["commit", "-m", message], repo_path)


def push_branch(repo_path: Path, branch_name: str, remote: str = "origin") -> None:
    """Отправляет ветку в удалённый репозиторий.
    
    Args:
        repo_path: Путь к репозиторию
        branch_name: Имя ветки для отправки
        remote: Имя удалённого репозитория (по умолчанию: origin)
    """
    run_git_command(["push", remote, branch_name], repo_path)


def create_release_candidate_branch(
    repo_path: Path, commit_id: str, branch_prefix: str = "release_candidate_"
) -> None:
    """Создаёт ветку release candidate со всеми текущими изменениями.
    
    Args:
        repo_path: Путь к репозиторию
        commit_id: ID исходного коммита для release candidate
        branch_prefix: Префикс для имени ветки
    """
    branch_name = f"{branch_prefix}{commit_id}"
    
    if not has_changes(repo_path):
        print("Нет изменений для коммита, пропускаем создание release candidate")
        return
    
    print(f"Создание ветки {branch_name}...")
    create_branch(repo_path, branch_name)
    
    print("Добавление изменений...")
    print("Создание коммита...")
    commit_all_changes(repo_path, f"Release candidate от коммита {commit_id}")
    
    print(f"Отправка {branch_name} в удалённый репозиторий...")
    push_branch(repo_path, branch_name)
    
    print(f"Ветка release candidate {branch_name} успешно создана и отправлена")

