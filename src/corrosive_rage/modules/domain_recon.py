# modules/domain_recon.py

# Importamos las nuevas herramientas de nuestro núcleo
from ..core.base import BaseModule
from ..core.utils import get_shodan_client, make_request

# Importamos las librerías externas que necesitemos
import whois
import re

class DomainReconModule(BaseModule):
    """
    Módulo para realizar reconocimiento de dominios.
    Hereda de BaseModule para obtener funcionalidades comunes.
    """
    def run(self) -> dict:
        """
        Ejecuta el proceso de reconocimiento de dominios.
        Ya no necesita 'target' ni 'config' como argumentos,
        porque están disponibles como 'self.target' y 'self.config'.
        """
        self.logger.info(f"[*] Iniciando reconocimiento de dominio para: {self.target}")

        # --- 1. Consulta WHOIS ---
        try:
            domain_info = whois.whois(self.target)
            # La lógica para extraer los datos sigue siendo la misma...
            registrar = domain_info.registrar
            creation_date = domain_info.creation_date
            expiration_date = domain_info.expiration_date
            
            emails_found = set()
            whois_text = str(domain_info)
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            emails_found.update(re.findall(email_pattern, whois_text))

            # ...pero en lugar de construir el diccionario a mano, usamos el método helper
            self.add_finding('whois', {
                'registrar': registrar[0] if isinstance(registrar, list) else registrar,
                'creation_date': str(creation_date[0]) if isinstance(creation_date, list) else str(creation_date),
                'expiration_date': str(expiration_date[0]) if isinstance(expiration_date, list) else str(expiration_date),
                'emails': list(emails_found)
            })
            # El logging ya está incluido en add_finding, pero podemos añadir un extra si queremos
            self.logger.info("[+] Información WHOIS encontrada.")
        except Exception as e:
            self.logger.error(f"[!] Error en la consulta WHOIS: {e}")

        # --- 2. Enumeración de Subdominios ---
        self.logger.info(f"[*] Buscando subdominios para {self.target}...")
        try:
            url = f"https://crt.sh/?q=%25.{self.target}&output=json"
            # Usamos nuestra utilidad 'make_request' en lugar de 'requests.get'
            response = make_request(url)
            
            if response:
                certs = response.json()
                subdomains = []
                for cert in certs:
                    name_value = cert.get('name_value', '')
                    for name in name_value.split('\n'):
                        if name and name not in subdomains:
                            subdomains.append(name)
                
                unique_subdomains = sorted(list(set(sub for sub in subdomains if sub and sub != self.target and not sub.startswith('*.'))))

                if unique_subdomains:
                    self.add_finding('subdomain_enumeration', {'subdomains': unique_subdomains, 'count': len(unique_subdomains)})
                    self.logger.info(f"[+] Se encontraron {len(unique_subdomains)} subdominios únicos.")
                else:
                    self.logger.info(f"[-] No se encontraron subdominios para {self.target}.")
            
        except Exception as e:
            self.logger.error(f"[!] Error en la enumeración de subdominios: {e}")

        # --- 3. Búsqueda en Shodan ---
        # ¡Mira qué limpio queda esto ahora!
        shodan_api_key = self.get_api_key('shodan')
        api = get_shodan_client(shodan_api_key)
        
        if api:
            try:
                host = api.host(self.target, history=False)
                self.add_finding('shodan_host_info', {
                    'country': host.get('country_name'),
                    'city': host.get('city'),
                    'org': host.get('org'),
                    'ports': host.get('ports'),
                    'vulns': list(host.get('vulns', []))[:5],
                    'ip_str': host.get('ip_str')
                })
                self.logger.info("[+] Información de Shodan encontrada.")
            except Exception as e:
                self.logger.error(f"[!] Error al consultar Shodan: {e}")
        else:
            # El warning de que la clave no está configurado ya lo gestiona 'get_api_key'
            self.logger.info("[!] Omitiendo búsqueda en Shodan.")

        # El método 'run' debe devolver los resultados, que la clase base ha estado construyendo.
        return self.results

# La función 'run' original ya no es necesaria aquí, la clase la encapsula todo.