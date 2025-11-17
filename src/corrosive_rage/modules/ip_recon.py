# modules/ip_recon.py

# Importamos las herramientas de nuestro núcleo
from ..core.base import BaseModule
from ..core.utils import get_shodan_client, make_request

# Importamos las librerías externas
import socket

class IpReconModule(BaseModule):
    """
    Módulo para realizar investigación de direcciones IP.
    Hereda de BaseModule para obtener funcionalidades comunes.
    """
    def run(self) -> dict:
        """
        Ejecuta el proceso de investigación de IPs.
        """
        self.logger.info(f"[*] Iniciando investigación de IP para: {self.target}")

        # --- 1. Geolocalización con ip-api.com ---
        try:
            # Usamos nuestra utilidad 'make_request' para una petición más robusta
            response = make_request(f"http://ip-api.com/json/{self.target}")
            if response:
                data = response.json()
                if data.get('status') == 'success':
                    self.add_finding('geolocation', {
                        'country': data.get('country'),
                        'region': data.get('regionName'),
                        'city': data.get('city'),
                        'isp': data.get('isp'),
                        'org': data.get('org'),
                        'query': data.get('query')
                    })
                    self.logger.info("[+] Información de geolocalización encontrada.")
                else:
                    self.logger.warning(f"Geolocalization API returned an error: {data.get('message')}")
        except Exception as e:
            self.logger.error(f"[!] Error en la consulta de geolocalización: {e}")

        # --- 2. DNS Inverso ---
        try:
            hostname, _, _ = socket.gethostbyaddr(self.target)
            self.add_finding('reverse_dns', {'hostname': hostname})
            self.logger.info(f"[+] DNS inverso encontrado: {hostname}")
        except socket.herror:
            self.logger.info("[-] No se encontró DNS inverso para esta IP.")
        except Exception as e:
            self.logger.error(f"[!] Error en la consulta de DNS inverso: {e}")

        # --- 3. Búsqueda en Shodan ---
        # ¡Fíjate qué idéntico y limpio es este bloque al del módulo de dominios!
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
                    'vulns': list(host.get('vulns', []))[:5]
                })
                self.logger.info("[+] Información de Shodan encontrada.")
            except Exception as e:
                self.logger.error(f"[!] Error al consultar Shodan: {e}")
        else:
            self.logger.info("[!] Omitiendo búsqueda en Shodan.")

        return self.results