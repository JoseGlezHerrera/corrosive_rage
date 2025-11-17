import argparse
import sys
import json
from pathlib import Path
from datetime import datetime
import configparser

# Mapeo de nombre -> clase, igual que antes
from corrosive_rage.modules import (
    domain_recon,
    ip_recon,
    email_recon,
    username_recon,
    dork_recon,
    breach_recon,
    company_recon,
    metadata_recon
)

MODULES = {
    'domain_recon': domain_recon.DomainReconModule,
    'ip_recon': ip_recon.IpReconModule,
    'email_recon': email_recon.EmailReconModule,
    'username_recon': username_recon.UsernameReconModule,
    'dork_recon': dork_recon.DorkReconModule,
    'breach_recon': breach_recon.BreachReconModule,
    'company_recon': company_recon.CompanyReconModule,
    'metadata_recon': metadata_recon.MetadataReconModule,
}

# 🔹 BASES de ruta bien definidas
PROJECT_ROOT = Path(__file__).resolve().parents[2]   # C:\...\corrosive_rage
SRC_ROOT = PROJECT_ROOT / "src"


def load_config():
    """Carga la configuración desde src/config/config.ini"""
    config = configparser.ConfigParser()
    default_config_path = SRC_ROOT / "config" / "config.ini"
    
    loaded = config.read(default_config_path)
    if not loaded:
        print(f"[!] Warning: No se pudo cargar el archivo de configuración en {default_config_path}.")
        print("[*] Usando configuración vacía.")
        config['APIs'] = {}
    
    return config


def main():
    parser = argparse.ArgumentParser(description="Corrosive's Rage - OSINT Toolkit CLI")
    parser.add_argument('-t', '--target', required=True, help='El objetivo a investigar (dominio, email, IP, etc.)')
    parser.add_argument('-m', '--module', required=True, help='El módulo a usar (ej: domain_recon, ip_recon)')

    args = parser.parse_args()
    target = args.target
    module_name = args.module

    print(f"[*] Iniciando investigación de '{module_name}' para el objetivo: '{target}'...")

    # 1️⃣ Verificar si el módulo existe en el diccionario
    if module_name not in MODULES:
        print(f"[!] Error: Módulo '{module_name}' no es válido o no está implementado.")
        sys.exit(1)

    try:
        # 2️⃣ Cargar configuración
        config = load_config()
        
        # 3️⃣ Instanciar el módulo correspondiente
        module_class = MODULES[module_name]
        module_instance = module_class(target=target, config=config)
        
        # 4️⃣ Ejecutar
        module_instance.run()
        
        # 5️⃣ Recoger resultados
        findings = module_instance.results

        output_data = {
            'target': target,
            'module': module_name,
            'timestamp': datetime.now().isoformat(),
            'findings': findings
        }

        # 6️⃣ Guardar en archivo SIEMPRE en <PROJECT_ROOT>/results
        results_dir = PROJECT_ROOT / "results"
        results_dir.mkdir(exist_ok=True)

        safe_target = "".join(c for c in target if c.isalnum() or c in ('.', '_')).rstrip()
        filename = results_dir / f"{safe_target}_{module_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=4, ensure_ascii=False)

        print(f"\n[+] ¡Investigación completada con éxito!")
        print(f"[*] Los resultados se han guardado en: {filename}\n")

        # 7️⃣ Imprimir JSON también para GUI (si usa stdout)
        print(json.dumps(output_data, indent=4, ensure_ascii=False))

    except Exception as e:
        print(f"\n[!] Error crítico durante la ejecución del módulo '{module_name}': {type(e).__name__}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()