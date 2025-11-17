# src/corrosive_rage/core/base.py
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import configparser

class BaseModule(ABC):
    """
    Clase base abstracta para todos los módulos de reconocimiento.
    Garantiza una interfaz común y proporciona utilidades compartidas.
    """
    def __init__(self, target: str, config: configparser.ConfigParser):
        self.target = target
        self.config = config
        # Creamos un logger específico para cada módulo (ej: 'DomainReconModule')
        self.logger = logging.getLogger(self.__class__.__name__)
        self.results = {
            'target': target,
            'module': self.__class__.__name__.lower().replace('module', ''),
            'findings': []
        }
        self.logger.info(f"Module initialized for target: {self.target}")

    @abstractmethod
    def run(self) -> Dict[str, Any]:
        """
        Método principal que ejecuta la lógica del módulo.
        Debe ser implementado por cada módulo concreto.
        """
        pass

    def add_finding(self, finding_type: str, data: Dict[str, Any]):
        """
        Añade un resultado a la lista de hallazgos de forma estandarizada.
        """
        self.results['findings'].append({'type': finding_type, 'data': data})
        self.logger.info(f"Finding added: {finding_type}")

    def get_api_key(self, service_name: str) -> Optional[str]:
        """
        Obtiene de forma segura una clave de API de la configuración.
        Verifica que no sea un placeholder.
        """
        try:
            # Intenta obtener la clave de la sección [APIs]
            api_key = self.config.get('APIs', f'{service_name}_api_key')
            if not api_key or api_key == f'TU_CLAVE_DE_API_DE_{service_name.upper()}_AQUI':
                self.logger.warning(f"API key for {service_name} not configured or is a placeholder.")
                return None
            return api_key
        except (configparser.NoSectionError, configparser.NoOptionError) as e:
            self.logger.error(f"Could not get API key for {service_name} from config: {e}")
            return None