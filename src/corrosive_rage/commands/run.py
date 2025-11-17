import click
import configparser
import json
from pathlib import Path

# Mapa de módulos: tipo -> clase (en string)
MODULE_MAP = {
    "domain": "domain_recon.DomainReconModule",
    "ip": "ip_recon.IpReconModule",
    "email": "email_recon.EmailReconModule",
    "username": "username_recon.UsernameReconModule",
    "breach": "breach_recon.BreachReconModule",
    "company": "company_recon.CompanyReconModule",
    "metadata": "metadata_recon.MetadataReconModule",
    "phone": "phone_recon.PhoneReconModule",
    "dork": "dork_recon.DorkReconModule"
}

@click.command()
@click.argument('module_type', type=click.Choice(list(MODULE_MAP.keys()), case_sensitive=False))
@click.argument('target')
@click.pass_context
def run(ctx, module_type, target):
    """
    Ejecuta un módulo de reconocimiento sobre un objetivo.
    Permite usar un archivo de configuración personalizado.
    """
    click.echo(f"[*] Running {module_type} module against target: {target}")

    # 1️⃣ Cargar configuración
    # Ruta por defecto: /config/config.ini
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    default_config_path = PROJECT_ROOT / "config" / "config.ini"

    # Ruta especificada por el usuario (si existe)
    config_file_path = ctx.obj.get('config_path', default_config_path)

    config = configparser.ConfigParser()
    loaded_files = config.read([default_config_path, config_file_path])

    if not loaded_files:
        click.echo(f"[!] No configuration file found. Using empty config.", err=True)
        config['APIs'] = {}

    # 2️⃣ Resolución dinámica de módulo
    try:
        module_path = MODULE_MAP.get(module_type.lower())
        if not module_path:
            click.echo(f"[!] Error: Module type '{module_type}' not found.", err=True)
            return

        module_name, class_name = module_path.split(".")
        click.echo(f"[*] Importing module: corrosive_rage.modules.{module_name}.{class_name}...")

        module = __import__(f"corrosive_rage.modules.{module_name}", fromlist=[class_name])
        module_class = getattr(module, class_name)

    except ImportError as e:
        click.echo(f"[!] Error: Could not import module '{module_type}'. Details: {e}", err=True)
        return

    # 3️⃣ Instanciar y ejecutar el módulo
    try:
        module_instance = module_class(target=target, config=config)
        results = module_instance.run()

        # 4️⃣ Imprimir los resultados en formato JSON
        click.echo(json.dumps(results, indent=2))

    except Exception as e:
        click.echo(f"[!] An unexpected error occurred: {type(e).__name__}: {e}", err=True)