from pathlib import Path


class Settings:
    # репозиторий, из которого забираем переменные и в который отправляем результат
    REMOTE_REPO_NAME = "config_templates"
    REMOTE_REPO_BRANCH = "main"
    REPO_URL = f"https://github.com/Akellazzz/{REMOTE_REPO_NAME}.git"
    VARIABLES_DIR = "variables"
    RESULTS_DIR = "results"

    # корневая директория, в которой находятся модули app и templates
    package_root = Path(__file__).resolve().parent.parent

    temp_dir = package_root / "temp"

    # локальная директория для репозитория
    repo_root = temp_dir / REMOTE_REPO_NAME
    variables_path = repo_root / VARIABLES_DIR
    results_path = repo_root / RESULTS_DIR


settings = Settings()
