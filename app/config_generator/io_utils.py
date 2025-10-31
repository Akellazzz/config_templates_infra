from pathlib import Path
from typing import List

from app.config_generator.models import AclEntry


def read_acl_entries(file_path: Path) -> List[AclEntry]:
    entries: List[AclEntry] = []
    if not file_path.exists():
        raise FileNotFoundError(f"Variables file not found: {file_path}")
    with file_path.open("r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split(";")]
            if len(parts) != 2 or not parts[0] or not parts[1]:
                raise ValueError(
                    f"Invalid ACL line in {file_path.name}: '{line}'. Expected '<ip>;<wildcard>'"
                )
            entries.append(AclEntry(ip=parts[0], wildcard=parts[1]))
    return entries


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def list_all_sites(variables_root: Path) -> List[str]:
    if not variables_root.exists():
        return []
    return [p.name for p in variables_root.iterdir() if p.is_dir()]


