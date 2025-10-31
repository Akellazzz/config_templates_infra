from pathlib import Path


class Settings:
    REPO_NAME = "config_templates"
    REPO_DEFAULT_BRANCH = "main"
    REPO_URL = f"https://github.com/Akellazzz/{REPO_NAME}.git"
    VARIABLES_RELPATH = Path("variables/vty_ACL/")
    TEMPLATES_RELPATH = Path("templates/vty_acl/")
    
    # Клонируем рабочий репозиторий внутрь пакета config_generator, чтобы очищать его после обработки вебхука
    repo_root = Path(__file__).resolve().parent / REPO_NAME
    result_config_dir = repo_root / "result_config"
    variables_root = repo_root / VARIABLES_RELPATH
    templates_root = Path(__file__).resolve().parent.parent / TEMPLATES_RELPATH


settings = Settings()


