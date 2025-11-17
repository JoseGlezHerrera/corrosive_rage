# src/corrosive_rage/modules/dork_recon.py

from ..core.base import BaseModule
from ..core.utils import make_request
import time

# NOTA: Usaremos la librería 'googlesearch-python', pero es importante saber
# que Google puede bloquear peticiones automatizadas si se abusa de ellas.
# Este módulo es para uso educativo y con moderación.

try:
    import googlesearch
except ImportError:
    googlesearch = None # Manejamos que no esté instalada

class DorkReconModule(BaseModule):
    """
    Módulo para ejecutar Google Dorks.
    Hereda de BaseModule para obtener funcionalidades comunes.
    """
    def run(self) -> dict:
        """
        Ejecuta el dork contra el objetivo.
        """
        if not googlesearch:
            self.logger.error("[!] La librería 'googlesearch-python' no está instalada. Ejecuta 'pip install googlesearch-python'.")
            self.add_finding('error', {'message': "The 'googlesearch-python' library is not installed."})
            return self.results

        self.logger.info(f"[*] Iniciando búsqueda de dork para: {self.target}")

        # Asumimos que el target es el dork completo, ej: "site:github.com \"password.txt\""
        dork_query = self.target

        try:
            # Ejecutamos la búsqueda y parseamos los resultados
            # El 'num' es el número de resultados a obtener. Lo ponemos bajo para no sobrecargar.
            # El 'stop' es el número de resultados a saltar, para paginar si es necesario.
            search_results = list(googlesearch.search(dork_query))

            if not search_results:
                self.logger.info(f"[-] No se encontraron resultados para el dork: {dork_query}")
                self.add_finding('no_results', {'dork': dork_query, 'message': 'No results found for this dork.'})
                return self.results

            # Estructuramos los resultados para que sean más útiles
            parsed_results = []
            for i, url in enumerate(search_results):
                parsed_results.append({
                    'result_number': i + 1,
                    'url': url
                })

            self.add_finding('dork_results', {
                'dork': dork_query,
                'result_count': len(parsed_results),
                'results': parsed_results
            })
            self.logger.info(f"[+] Se encontraron {len(parsed_results)} resultados para el dork.")

        except Exception as e:
            self.logger.error(f"[!] Error al ejecutar el dork: {e}")
            self.add_finding('error', {'message': f'An error occurred during the search: {e}'})

        # Pausa para no ser bloqueado por Google demasiado rápido
        time.sleep(2)

        return self.results