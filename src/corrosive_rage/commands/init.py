# src/corrosive_rage/commands/init.py

import click
from pathlib import Path

@click.command()
@click.argument("project_name")
@click.option("--client", help="Client name for the project.")
@click.option("--scope", help="Scope of the project.")
def init(project_name, client, scope):
    """Initializes a new pentesting project."""
    project_path = Path("./projects") / project_name
    project_path.mkdir(parents=True, exist_ok=True)
    
    project_file = project_path / "project.yml"
    if project_file.exists():
        click.echo(f"Project '{project_name}' already exists.")
        return

    # Lógica para crear el archivo project.yml...
    # (Aquí iría el código original de tu comando init)
    click.echo(f"Project '{project_name}' created at {project_path}")