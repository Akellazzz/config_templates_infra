"""Настройка логирования для всего приложения."""
import logging
import sys

from app.app_config import settings


def setup_logging(level: int = logging.INFO) -> None:
    """Настраивает логирование для приложения.
    
    Args:
        level: Уровень логирования (по умолчанию INFO)
    """

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(settings.temp_dir / "app.log")
        ],
        force=True,
    )


setup_logging()


def get_logger(name: str) -> logging.Logger:
    """Возвращает логгер с указанным именем.
    
    Args:
        name: Имя логгера (обычно __name__)
    
    Returns:
        Настроенный логгер
    """
    return logging.getLogger(name)

