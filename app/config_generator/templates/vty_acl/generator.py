from pathlib import Path
from typing import List

from app.config_generator.io_utils import ensure_dir, list_all_sites
from app.config_generator.render import render_template
from app.app_config import settings
from app.logger import get_logger

from dataclasses import dataclass
from app.config_generator.core import ConfigGenerator

logger = get_logger(__name__)


@dataclass
class AclEntry:
    ip: str
    wildcard: str


class Generator(ConfigGenerator):
    def generate_config(self) -> None:
        """Генерация VTY ACL для всех сайтов."""
        variables_file = "acl_ssh_dc.txt"
        results_dir = settings.results_path
        ensure_dir(results_dir)

        variables_vty_acl_dir = settings.variables_path / "vty_ACL/"
        sites: List[str] = list_all_sites(variables_vty_acl_dir)
        if not sites:
            # raise FileNotFoundError(
            #     f"No sites found under: {variables_vty_acl_dir}"
            # )
            logger.warning(f"No sites found under: {variables_vty_acl_dir}")
        self._generate_for_sites(
            sites=sites,
            variables_file=variables_file,
            results_dir=results_dir,
            template_dir=Path(__file__).resolve().parent,
            template_name="template.j2",
            variables_vty_acl_dir=variables_vty_acl_dir,
        )

    def _read_acl_entries(self, file_path: Path) -> List[AclEntry]:
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

    def _generate_for_sites(
        self,
        sites: List[str],
        variables_file: str,
        results_dir: Path,
        template_dir: Path,
        template_name: str,
        variables_vty_acl_dir: Path,
    ) -> None:
        """Генерация конфигурации для всех сайтов."""

        for site in sites:
            variables_path = variables_vty_acl_dir / site / variables_file
            acl_entries = self._read_acl_entries(variables_path)

            context = {
                "site": site,
                "acl_ssh_dc": acl_entries,
            }

            rendered = render_template(
                template_dir=template_dir,
                template_name=template_name,
                context=context,
            )

            final_name = f"vty_ACL_{site}.txt"

            output_path = Path(final_name)
            if not output_path.is_absolute():
                output_path = results_dir / output_path

            with output_path.open("w", encoding="utf-8", newline="\n") as f:
                f.write(rendered.rstrip() + "\n")

            logger.info(f"Rendered configuration written to: {output_path}")
