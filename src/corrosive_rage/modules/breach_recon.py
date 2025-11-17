# src/corrosive_rage/modules/breach_recon.py

# Importamos las herramientas de nuestro núcleo
from ..core.base import BaseModule
from ..core.utils import make_request

# Importamos las librerías externas
import json

class BreachReconModule(BaseModule):
    """
    Módulo para verificar si un email ha aparecido en filtraciones de datos.
    Hereda de BaseModule para obtener funcionalidades comunes.
    """
    def run(self) -> dict:
        """
        Ejecuta la consulta en la API de Have I Been Pwned.
        """
        self.logger.info(f"[*] Iniciando búsqueda de filtraciones para el email: {self.target}")

        # 1. Obtener la clave de API de Have I Been Pwned
        # La API de HIBP requiere una clave para casi todas sus consultas.
        api_key = self.get_api_key('haveibeenpwned')
        if not api_key:
            self.logger.warning("[!] API key for HaveIBeenPwned not configured. Cannot proceed.")
            self.add_finding('error', {'message': 'HaveIBeenPwned API key is missing.'})
            return self.results

        # 2. Construir la petición a la API
        # La API de "breached account" de HIBP es perfecta para esto.
        # La documentación oficial: https://haveibeenpwned.com/API/v3#BreachedAccount
        api_url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{self.target}"
        headers = {
            'hibp-api-key': api_key,
            'User-Agent': 'Corrosive-Rage-OSINT-Framework'
        }

        try:
            # 3. Ejecutar la petición usando nuestra utilidad
            response = make_request(api_url, headers=headers)
            
            if response:
                breaches = response.json()
                if breaches:
                    # 4. Procesar los resultados y añadirlos como un hallazgo
                    self.add_finding('breaches_found', {
                        'email': self.target,
                        'breach_count': len(breaches),
                        'details': breaches
                    })
                    self.logger.info(f"[+] Se encontraron {len(breaches)} filtraciones para {self.target}.")
                else:
                    self.logger.info(f"[-] No se encontraron filtraciones para el email {self.target}.")
                    # Añadimos un hallazgo para indicar que está limpio
                    self.add_finding('no_breaches_found', {'email': self.target, 'message': 'Email not found in any known breaches.'})

        except Exception as e:
            self.logger.error(f"[!] Error al consultar la API de HaveIBeenPwned: {e}")
            self.add_finding('error', {'message': f'Failed to query HaveIBeenPwned API: {e}'})

        return self.results