# src/corrosive_rage/cli.py (versión COMPLETA y FINAL)

import click
from pathlib import Path

# Importamos todos los comandos DIRECTAMENTE desde sus archivos
from .commands.init import init
from .commands.project import project       
from .commands.report import report        
from .commands.run import run              

@click.group()
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to a custom configuration file.",
    default=Path("config.ini")
)
@click.pass_context
def cli(ctx, config_path):
    """A modular CLI tool for OSINT and reconnaissance."""
    ctx.ensure_object(dict)
    ctx.obj['config_path'] = config_path

# Añadimos todos los comandos usando las funciones que importamos directamente
cli.add_command(init)
cli.add_command(project)      
cli.add_command(report)
cli.add_command(run)