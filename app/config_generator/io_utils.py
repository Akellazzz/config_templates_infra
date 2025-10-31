from pathlib import Path
from typing import List


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def list_all_sites(variables_path: Path) -> List[str]:
    if not variables_path.exists():
        return []
    return [p.name for p in variables_path.iterdir() if p.is_dir()]
