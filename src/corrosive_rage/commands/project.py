# src/corrosive_rage/commands/project.py

import click

@click.group()
def project():
    """Manages pentesting projects."""
    pass

@project.command()
@click.argument("project_name")
def create(project_name):
    """Creates a new project (alias for init)."""
    # Lógica para crear un proyecto, similar al comando init
    click.echo(f"Creating project '{project_name}'...")