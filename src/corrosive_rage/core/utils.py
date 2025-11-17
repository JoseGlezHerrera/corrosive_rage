# src/corrosive_rage/core/utils.py
import shodan
import requests
import logging
from typing import Optional, Dict, Any

# Configuramos un logger para las utilidades
logger = logging.getLogger(__name__)

def get_shodan_client(api_key: Optional[str]) -> Optional[shodan.Shodan]:
    """
    Crea y devuelve un cliente de Shodan si la clave de API es válida.
    Maneja los errores de inicialización.
    """
    if not api_key:
        logger.warning("Shodan API key not provided.")
        return None
    try:
        client = shodan.Shodan(api_key)
        # A veces, la API no da un error hasta la primera llamada, pero una validación básica es buena.
        logger.info("Shodan client initialized successfully.")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Shodan client: {e}")
        return None

def make_request(url: str, method: str = 'GET', timeout: int = 10, **kwargs) -> Optional[requests.Response]:
    """
    Realiza una petición HTTP con manejo básico de errores y logging.
    Devuelve el objeto Response o None si falla.
    """
    try:
        response = requests.request(method, url, timeout=timeout, **kwargs)
        response.raise_for_status()  # Lanza una excepción para códigos de error (4xx o 5xx)
        logger.debug(f"Request to {url} successful with status {response.status_code}.")
        return response
    except requests.exceptions.Timeout:
        logger.error(f"Request timed out for URL: {url}")
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error for URL {url}: {e}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for URL {url}: {e}")
    return None
