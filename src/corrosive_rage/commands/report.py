# src/corrosive_rage/commands/report.py

import click
from pathlib import Path

@click.command()
@click.option("--project", help="Project name to generate the report for.")
@click.option("--template", default="report_template.md.j2", help="Jinja2 template to use.")
@click.option("--output", type=click.Path(path_type=Path), help="Output file path.")
def report(project, template, output):
    """Generates a pentesting report from a template."""
    # Lógica para generar el informe...
    click.echo("Generating report...")