# src/corrosive_rage/modules/phone_recon.py

from ..core.base import BaseModule
from ..core.utils import make_request
import numverify

class PhoneReconModule(BaseModule):
    """
    Módulo para validar y obtener información de números de teléfono.
    Hereda de BaseModule para obtener funcionalidades comunes.
    """
    def run(self) -> dict:
        """
        Ejecuta la validación e investigación del número de teléfono.
        """
        self.logger.info(f"[*] Iniciando investigación de teléfono para: {self.target}")

        # 1. Obtener la clave de API de Numverify
        api_key = self.get_api_key('numverify')
        if not api_key:
            self.logger.warning("[!] API key for Numverify not configured. Cannot proceed.")
            self.add_finding('error', {'message': 'Numverify API key is missing.'})
            return self.results

        # 2. Inicializar el cliente de la API
        try:
            client = numverify.Client(api_key=api_key)
        except Exception as e:
            self.logger.error(f"[!] Error al inicializar el cliente de Numverify: {e}")
            self.add_finding('error', {'message': f'Failed to initialize Numverify client: {e}'})
            return self.results

        # 3. Realizar la consulta a la API
        try:
            # La librería `numverify` se encarga de la petición HTTP
            result = client.get_number_info(self.target)

            if result and result.get('valid'):
                # 4. Procesar y añadir los hallazgos
                self.add_finding('phone_info', {
                    'phone_number': result.get('international_format'),
                    'country': result.get('country_name'),
                    'location': result.get('location'),
                    'carrier': result.get('carrier'),
                    'line_type': result.get('line_type'),
                    'is_valid': result.get('valid')
                })
                self.logger.info(f"[+] Información del teléfono encontrada para {self.target}.")
            else:
                self.logger.info(f"[-] El número de teléfono {self.target} no es válido o no se encontró información.")
                self.add_finding('invalid_phone', {
                    'phone_number': self.target,
                    'message': 'The phone number is invalid or no data was found.'
                })

        except Exception as e:
            self.logger.error(f"[!] Error al consultar la API de Numverify: {e}")
            self.add_finding('error', {'message': f'Failed to query Numverify API: {e}'})

        return self.results