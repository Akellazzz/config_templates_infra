import argparse
from pathlib import Path
from typing import Iterable, List

from app.config_generator.io_utils import ensure_dir, list_all_sites, read_acl_entries
from app.config_generator.render import render_template
from app.app_config import settings


def generate_for_sites(
    sites: List[str],
    variables_file: str,
    results_dir: Path,
    template_dir: Path,
    template_name: str,
    output_name: str | None,
) -> None:
    ensure_dir(results_dir)

    for site in sites:
        variables_path = settings.variables_root_vty_acl / site / variables_file
        acl_entries = read_acl_entries(variables_path)

        context = {
            "site": site,
            "acl_ssh_dc": acl_entries,
        }

        rendered = render_template(
            template_dir=template_dir,
            template_name=template_name,
            context=context,
        )

        if output_name:
            try:
                candidate_name = output_name.format(site=site)
            except Exception:
                candidate_name = output_name
            if len(sites) > 1 and "{site}" not in output_name:
                p = Path(candidate_name)
                stem = p.stem
                suffix = p.suffix
                candidate_name = f"{stem}_{site}{suffix}"
            final_name = candidate_name
        else:
            final_name = f"vty_ACL_{site}.txt"

        output_path = Path(final_name)
        if not output_path.is_absolute():
            output_path = results_dir / output_path

        with output_path.open("w", encoding="utf-8", newline="\n") as f:
            f.write(rendered.rstrip() + "\n")

        print(f"Rendered configuration written to: {output_path}")


def generate_config(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Render vty ACL configuration using Jinja2 and variables."
    )
    parser.add_argument(
        "--site",
        default="ALL",
        help=(
            "Site name(s). Single (HQ), comma-separated (HQ,DC1) or 'ALL' to process"
        ),
    )
    parser.add_argument(
        "--variables-file",
        default="acl_ssh_dc.txt",
        help="Variables filename inside the site folder",
    )
    parser.add_argument(
        "--results-dir",
        default=str(settings.results_path),
        help="Directory to write rendered configuration",
    )
    parser.add_argument(
        "--output-name",
        default=None,
        help="Optional output file name. Supports {site} placeholder",
    )
    parser.add_argument(
        "--template-dir",
        default=str(settings.templates_root_vty_acl),
        help="Directory containing Jinja2 template",
    )
    parser.add_argument(
        "--template-name",
        default="vty_ACL.j2",
        help="Template filename",
    )

    args = parser.parse_args(list(argv) if argv is not None else None)

    raw_site = (args.site or "").strip()
    if raw_site.upper() == "ALL":
        sites: List[str] = list_all_sites(settings.variables_root_vty_acl)
        if not sites:
            raise FileNotFoundError(
                f"No sites found under: {settings.variables_root_vty_acl}"
            )
    elif "," in raw_site:
        sites = [s.strip() for s in raw_site.split(",") if s.strip()]
    else:
        sites = [raw_site or "HQ"]

    template_dir = Path(args.template_dir)
    if not template_dir.is_absolute():
        template_dir = settings.repo_root / template_dir

    results_dir = Path(args.results_dir)
    if not results_dir.is_absolute():
        results_dir = settings.repo_root / results_dir

    generate_for_sites(
        sites=sites,
        variables_file=args.variables_file,
        results_dir=results_dir,
        template_dir=template_dir,
        template_name=args.template_name,
        output_name=args.output_name,
    )


if __name__ == "__main__":
    generate_config()
