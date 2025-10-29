from pathlib import Path


class Settings:
    REPO_NAME = "config_templates"
    REPO_URL = "https://github.com/Akellazzz/config_templates.git"
    DEFAULT_BRANCH = "develop"
    # Path to repo is now one level up since we're in vty_acl/
    DEST_DIR = (Path(__file__).resolve().parent.parent / REPO_NAME).as_posix()


# Создание экземпляра настроек
settings = Settings()