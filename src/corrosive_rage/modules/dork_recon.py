# src/corrosive_rage/modules/dork_recon.py

from ..core.base import BaseModule
from ..core.utils import make_request  # keep import for future HTTP-based extensions
import time

# NOTA: Históricamente este módulo usaba la librería 'googlesearch-python',
# pero Google bloquea muy a menudo las peticiones automatizadas y suele
# devolver 0 resultados. Para hacerlo más fiable, ahora usamos
# 'duckduckgo-search' como motor principal y dejamos 'googlesearch-python'
# como opción de respaldo si está instalada.

try:
    from ddgs import DDGS  # Motor principal (no requiere API key)
except ImportError:  # pragma: no cover - manejamos la ausencia gracefully
    DDGS = None

try:
    import googlesearch  # Motor de respaldo (puede fallar o dar pocos resultados)
except ImportError:
    googlesearch = None


class DorkReconModule(BaseModule):
    """
    Módulo para ejecutar búsquedas tipo "dork" sobre un objetivo.
    Hereda de BaseModule para obtener funcionalidades comunes.
    """

    def run(self) -> dict:
        """
        Ejecuta el dork contra el objetivo (self.target) usando motores
        de búsqueda web y devuelve los resultados normalizados en
        self.results.
        """

        dork_query = (self.target or "").strip()

        if not dork_query:
            self.logger.error("[!] El dork/objetivo está vacío.")
            self.add_finding(
                "error",
                {
                    "message": "Empty dork/target received. Please provide a valid query."
                },
            )
            return self.results

        self.logger.info(f"[*] Iniciando búsqueda de dork para: {dork_query}")

        # 1) Intentamos primero con DuckDuckGo (recomendado, más estable)
        if DDGS is not None:
            try:
                self.logger.info("[*] Usando motor: DuckDuckGo (duckduckgo-search)")
                with DDGS() as ddgs:
                    raw_results = list(
                        ddgs.text(
                            dork_query,
                            max_results=20,  # Número razonable para OSINT
                        )
                    )

                if raw_results:
                    parsed_results = []
                    for i, item in enumerate(raw_results, start=1):
                        parsed_results.append(
                            {
                                "result_number": i,
                                "title": item.get("title"),
                                # duckduckgo_search suele exponer la URL en 'href'
                                "url": item.get("href") or item.get("link"),
                                "snippet": item.get("body") or item.get("snippet"),
                            }
                        )

                    self.add_finding(
                        "dork_results",
                        {
                            "dork": dork_query,
                            "engine": "duckduckgo",
                            "result_count": len(parsed_results),
                            "results": parsed_results,
                        },
                    )
                    self.logger.info(
                        f"[+] Se encontraron {len(parsed_results)} resultados (DuckDuckGo)."
                    )

                    # Pausa ligera para no hacer spam al motor
                    time.sleep(1)
                    return self.results
                else:
                    self.logger.info(
                        f"[-] DuckDuckGo no devolvió resultados para: {dork_query}"
                    )

            except Exception as e:
                self.logger.error(f"[!] Error usando DuckDuckGo: {e}")
                self.add_finding(
                    "error",
                    {
                        "message": f"An error occurred during DuckDuckGo search: {e}",
                        "engine": "duckduckgo",
                    },
                )

        # 2) Si no pudimos usar DuckDuckGo o no dio nada, probamos con googlesearch
        if googlesearch is not None:
            try:
                self.logger.info("[*] Usando motor de respaldo: googlesearch-python")
                search_results = list(googlesearch.search(dork_query))

                if search_results:
                    parsed_results = []
                    for i, url in enumerate(search_results, start=1):
                        parsed_results.append(
                            {
                                "result_number": i,
                                "url": url,
                            }
                        )

                    self.add_finding(
                        "dork_results",
                        {
                            "dork": dork_query,
                            "engine": "googlesearch",
                            "result_count": len(parsed_results),
                            "results": parsed_results,
                        },
                    )
                    self.logger.info(
                        f"[+] Se encontraron {len(parsed_results)} resultados (googlesearch-python)."
                    )
                else:
                    self.logger.info(
                        f"[-] googlesearch-python no devolvió resultados para: {dork_query}"
                    )
                    self.add_finding(
                        "no_results",
                        {
                            "dork": dork_query,
                            "engine": "googlesearch",
                            "message": "No results found for this dork.",
                        },
                    )

            except Exception as e:
                self.logger.error(f"[!] Error al ejecutar el dork con googlesearch: {e}")
                self.add_finding(
                    "error",
                    {
                        "message": f"An error occurred during googlesearch search: {e}",
                        "engine": "googlesearch",
                    },
                )
        else:
            if DDGS is None:
                # No tenemos ningún motor disponible
                self.logger.error(
                    "[!] No hay librerías de búsqueda instaladas. "
                    "Instala al menos 'duckduckgo-search' (recomendado) "
                    "o 'googlesearch-python'."
                )
                self.add_finding(
                    "error",
                    {
                        "message": (
                            "No search backend available. Install 'duckduckgo-search' "
                            "(recommended) or 'googlesearch-python'."
                        )
                    },
                )
            else:
                # DDGS está instalado pero no devolvió nada ni lanzó error
                self.add_finding(
                    "no_results",
                    {
                        "dork": dork_query,
                        "engine": "duckduckgo",
                        "message": "No results returned by DuckDuckGo.",
                    },
                )

        time.sleep(1)
        return self.results