from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined


def render_template(template_dir: Path, template_name: str, context: dict) -> str:
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        autoescape=False,
    )
    template = env.get_template(template_name)
    return template.render(**context)


