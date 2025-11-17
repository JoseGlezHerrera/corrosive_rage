# src/corrosive_rage/modules/username_recon.py

# Importamos las herramientas de nuestro núcleo
from ..core.base import BaseModule
from ..core.utils import make_request

# Importamos las librerías externas
import concurrent.futures

# La lista de sitios sigue siendo una constante a nivel de módulo
SITES = [
    {'name': 'Twitter', 'url_check': 'https://twitter.com/{}', 'url_profile': 'https://twitter.com/{}'},
    {'name': 'Instagram', 'url_check': 'https://www.instagram.com/{}/', 'url_profile': 'https://www.instagram.com/{}/'},
    {'name': 'GitHub', 'url_check': 'https://github.com/{}', 'url_profile': 'https://github.com/{}'},
    {'name': 'TikTok', 'url_check': 'https://www.tiktok.com/@{}', 'url_profile': 'https://www.tiktok.com/@{}'},
    {'name': 'YouTube', 'url_check': 'https://www.youtube.com/{}', 'url_profile': 'https://www.youtube.com/{}'},
    {'name': 'Reddit', 'url_check': 'https://www.reddit.com/user/{}', 'url_profile': 'https://www.reddit.com/user/{}'},
    {'name': 'LinkedIn', 'url_check': 'https://www.linkedin.com/in/{}', 'url_profile': 'https://www.linkedin.com/in/{}'},
    {'name': 'Facebook', 'url_check': 'https://www.facebook.com/{}', 'url_profile': 'https://www.facebook.com/{}'},
]

# La función de comprobación ahora es "pura" y recibe el logger como parámetro.
def check_username(username, site, logger):
    """
    Verifica si un nombre de usuario existe en un sitio específico.
    """
    url = site['url_check'].format(username)
    try:
        response = make_request(url, method='HEAD')
        
        if response and response.status_code == 200:
            logger.info(f"[+] Perfil encontrado en {site['name']}")
            return {'site': site['name'], 'url': site['url_profile'].format(username)}
            
    except Exception as e:
        # Manejo de errores más descriptivo
        if hasattr(e, 'response'):
            if e.response.status_code == 404:
                logger.info(f"[-] Perfil no encontrado en {site['name']}.")
            elif e.response.status_code == 403:
                logger.info(f"[-] Acceso bloqueado por {site['name']} (protección anti-bots).")
            else:
                logger.info(f"[-] Error HTTP {e.response.status_code} en {site['name']}.")
        else:
            logger.debug(f"[-] No se pudo verificar {site['name']}: {e}")
        pass
    return None

class UsernameReconModule(BaseModule):
    """
    Módulo para realizar investigación de nombres de usuario en redes sociales.
    Hereda de BaseModule para obtener funcionalidades comunes.
    """
    def run(self) -> dict:
        """
        Ejecuta la búsqueda de nombres de usuario en paralelo.
        """
        self.logger.info(f"[*] Iniciando búsqueda de nombre de usuario para: {self.target}")
        found_profiles = []
        
        # Usamos ThreadPoolExecutor para hacer las peticiones en paralelo.
        # La diferencia clave es que pasamos 'self.logger' a cada worker.
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(check_username, self.target, site, self.logger) 
                for site in SITES
            ]
            
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    found_profiles.append(result)
        
        if found_profiles:
            self.add_finding('user_profiles', found_profiles) # <-- Corregido aquí también
            self.logger.info(f"[+] Se encontraron {len(found_profiles)} perfiles para el usuario '{self.target}'.")
        else:
            self.logger.info(f"[-] No se encontraron perfiles públicos para el usuario '{self.target}'.")
            
        return self.results