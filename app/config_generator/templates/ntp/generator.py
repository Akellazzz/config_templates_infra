from pathlib import Path
from typing import List

from app.config_generator.io_utils import ensure_dir, list_all_sites
from app.config_generator.render import render_template
from app.app_config import settings

from dataclasses import dataclass


@dataclass
class NTPServer:
    ip: str
    priority: str


def read_ntp_servers(file_path: Path) -> List[NTPServer]:
    entries: List[NTPServer] = []
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
                    f"Invalid ACL line in {file_path.name}: '{line}'. Expected '<ip>;<priority>'"
                )
            entries.append(NTPServer(ip=parts[0], priority=parts[1]))
    return entries


def generate_for_sites(
    sites: List[str],
    variables_file: str,
    results_dir: Path,
    template_dir: Path,
    template_name: str,
    variables_ntp_servers_dir: Path,
) -> None:

    
    for site in sites:
        variables_path = variables_ntp_servers_dir / site / variables_file
        ntp_servers = read_ntp_servers(variables_path)

        context = {
            "site": site,
            "ntp_servers": ntp_servers,
        }

        rendered = render_template(
            template_dir=template_dir,
            template_name=template_name,
            context=context,
        )

        final_name = f"NTP_servers_{site}.txt"

        output_path = Path(final_name)
        if not output_path.is_absolute():
            output_path = results_dir / output_path

        with output_path.open("w", encoding="utf-8", newline="\n") as f:
            f.write(rendered.rstrip() + "\n")

        print(f"Rendered configuration written to: {output_path}")


def generate_config() -> None:
    """Генерация конфигурации для всех сайтов."""
    variables_file = "ntp_servers.txt"
    results_dir = settings.results_path
    ensure_dir(results_dir)

    variables_ntp_servers_dir = settings.variables_path / "ntp_servers/"
    sites: List[str] = list_all_sites(variables_ntp_servers_dir)
    if not sites:
        print(f"No sites found under: {variables_ntp_servers_dir}")
        return
    generate_for_sites(
        sites=sites,
        variables_file=variables_file,
        results_dir=results_dir,
        template_dir=Path(__file__).resolve().parent,
        template_name="template.j2",
        variables_ntp_servers_dir=variables_ntp_servers_dir,
    )


