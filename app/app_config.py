from pathlib import Path


class Settings:
    # корневая директория, в которой находятся модули app и templates
    package_root = Path(__file__).resolve().parent.parent

    # репозиторий, из которого забираем переменные и в который отправляем результат
    REMOTE_REPO_NAME = "config_templates"
    REMOTE_REPO_BRANCH = "main"
    REPO_URL = f"https://github.com/Akellazzz/{REMOTE_REPO_NAME}.git"
    VARIABLES_DIR = "variables"
    RESULTS_DIR = "results"

    # локальная директория для репо
    repo_root = package_root / REMOTE_REPO_NAME
    variables_path = repo_root / VARIABLES_DIR
    results_path = repo_root / RESULTS_DIR

    # # VTY ACL
    # TEMPLATES_ROOT = package_root / "app" / "config_generator" / "templates"
    # TEMPLATES_RELPATH_VTY_ACL = Path("app/config_generator/templates/vty_acl/")
    # variables_root_vty_acl = repo_root / "variables/template/"
    # templates_root_vty_acl = package_root / TEMPLATES_RELPATH_VTY_ACL

    # # NTP
    # TEMPLATES_RELPATH_NTP = Path("app/config_generator/templates/NTP/")
    # variables_root_ntp = repo_root / VARIABLES_RELPATH_NTP
    # templates_root_ntp = package_root / TEMPLATES_RELPATH_NTP


settings = Settings()
