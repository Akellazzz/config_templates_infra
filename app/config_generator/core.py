from abc import ABC, abstractmethod
from pathlib import Path
import importlib
import inspect
from app.logger import get_logger

logger = get_logger(__name__)


class ConfigGenerator(ABC):
    """Базовый интерфейс генератора конфигураций.

    Каждый генератор в app/config_generator/templates/<name>/generator.py
    должен предоставить класс-наследник generate_config() с аргументами:
    - variables_file: str - имя файла с переменными
    - results_dir: Path - директория для сохранения результатов
    - template_dir: Path - директория с шаблонами
    - template_name: str - имя шаблона
    - variables_dir: Path - директория с переменными
    """

    @abstractmethod
    def generate_config() -> None:
        """Выполнить генерацию конфигураций"""
        raise NotImplementedError


def get_generators() -> list[ConfigGenerator]:
    """Находит генераторы в templates/*/generator.py и возвращает список классов-наследников ConfigGenerator."""
    generators: list[ConfigGenerator] = []
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
            logger.warning(f"Пропуск {module_name}: импорт неудачен ({exc})")
            continue

        found = False
        for _, obj in inspect.getmembers(mod, inspect.isclass):
            if issubclass(obj, ConfigGenerator) and obj is not ConfigGenerator:
                generators.append(obj())
                found = True
        if found:
            continue

        gen = getattr(mod, "Generator", None)
        if gen and issubclass(gen, ConfigGenerator):
            generators.append(gen())
        else:
            logger.warning(f"Пропуск {module_name}: нет класса-наследника ConfigGenerator")

    return generators


