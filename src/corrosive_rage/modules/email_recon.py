# src/corrosive_rage/modules/email_recon.py

# Importamos las herramientas de nuestro núcleo
from ..core.base import BaseModule

# Importamos las librerías externas
import requests
import hashlib
from urllib.parse import quote

class EmailReconModule(BaseModule):
    """
    Módulo para realizar investigación de direcciones de correo electrónico.
    Hereda de BaseModule para obtener funcionalidades comunes.
    """
    def run(self) -> dict:
        """
        Ejecuta el proceso de investigación de emails.
        """
        self.logger.info(f"[*] Iniciando investigación de email para: {self.target}")

        # --- 1. Comprobación de Gravatar ---
        try:
            email_hash = hashlib.md5(self.target.lower().strip().encode()).hexdigest()
            gravatar_url = f"https://www.gravatar.com/avatar/{email_hash}?d=404&s=80"
            
            # Nota: Usamos requests.head directamente aquí.
            # Nuestra utilidad 'make_request' está pensada para respuestas 2xx exitosas.
            # En este caso, un 404 es un resultado válido (no hay perfil), así que manejamos la lógica específica aquí.
            response = requests.head(gravatar_url, timeout=5)
            if response.status_code == 200:
                self.add_finding('gravatar_profile', {'profile_url': f"https://www.gravatar.com/{email_hash}"})
                self.logger.info("[+] Perfil de Gravatar encontrado.")
        except requests.RequestException as e:
            self.logger.error(f"[!] Error al comprobar Gravatar: {e}")

        # --- 2. Generación de Enlaces para Investigación Manual ---
        try:
            encoded_email = quote(self.target)
            search_links = [
                {'name': 'Google', 'url': f"https://www.google.com/search?q=\"{encoded_email}\""},
                {'name': 'Bing', 'url': f"https://www.bing.com/search?q=\"{encoded_email}\""},
                {'name': 'DuckDuckGo', 'url': f"https://duckduckgo.com/?q=\"{encoded_email}\""},
                {'name': 'Facebook', 'url': f"https://www.facebook.com/search/people/?q={encoded_email}"},
                {'name': 'Twitter', 'url': f"https://twitter.com/search?q=\"{encoded_email}\"&f=user"}
            ]
            self.add_finding('search_engine_links', search_links)
            self.logger.info("[+] Enlaces de búsqueda generados para investigación manual.")
        except Exception as e:
            self.logger.error(f"[!] Error al generar enlaces de búsqueda: {e}")

        # --- 3. Generar enlace para Have I Been Pwned ---
        try:
            self.add_finding('have_i_been_pwned_link', {'search_url': f"https://haveibeenpwned.com/Account/{self.target}"})
            self.logger.info("[+] Enlace para Have I Been Pwned generado.")
        except Exception as e:
            self.logger.error(f"[!] Error al generar el enlace de Have I Been Pwned: {e}")
        
        return self.results