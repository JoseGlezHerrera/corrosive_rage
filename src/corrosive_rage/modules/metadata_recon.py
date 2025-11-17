# src/corrosive_rage/modules/metadata_recon.py

from ..core.base import BaseModule
from ..core.utils import make_request
import requests
from pathlib import Path
import tempfile
import os

# Importamos las librerías de metadatos
try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None # Manejamos que no esté instalada

try:
    from docx import opendocx
except ImportError:
    opendocx = None # Manejamos que no esté instalada

class MetadataReconModule(BaseModule):
    """
    Módulo para analizar metadatos de documentos.
    Hereda de BaseModule para obtener funcionalidades comunes.
    """
    def run(self) -> dict:
        """
        Ejecuta el análisis de metadatos.
        """
        self.logger.info(f"[*] Iniciando análisis de metadatos para: {self.target}")
        
        # Asumimos que el target es una URL a un documento
        if not self.target.startswith(('http://', 'https://')):
            self.logger.error("[!] El objetivo debe ser una URL válida a un documento.")
            self.add_finding('error', {'message': 'Target must be a valid URL.'})
            return self.results

        try:
            # 1. Descargar el documento a un archivo temporal
            response = make_request(self.target)
            if not response:
                self.add_finding('error', {'message': f'Could not download file from {self.target}'})
                return self.results

            # 2. Determinar el tipo de archivo por el Content-Type o la extensión
            content_type = response.headers.get('content-type', '')
            file_ext = ''
            if 'pdf' in content_type:
                file_ext = '.pdf'
            elif 'wordprocessingml.document' in content_type:
                file_ext = '.docx'
            else:
                # Fallback: intentar por la extensión en la URL
                if self.target.endswith('.pdf'):
                    file_ext = '.pdf'
                elif self.target.endswith('.docx'):
                    file_ext = '.docx'

            if not file_ext:
                self.logger.warning("[!] No se pudo determinar el tipo de archivo (PDF/DOCX).")
                self.add_finding('error', {'message': 'Could not determine file type (PDF/DOCX).'})
                return self.results

            # 3. Guardar en un archivo temporal
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
                tmp_file.write(response.content)
                tmp_file_path = Path(tmp_file.name)

            # 4. Extraer metadatos según el tipo de archivo
            metadata = {}
            if file_ext == '.pdf' and PdfReader:
                metadata = self._extract_pdf_metadata(tmp_file_path)
            elif file_ext == '.docx' and opendocx:
                metadata = self._extract_docx_metadata(tmp_file_path)
            else:
                self.logger.warning(f"[!] No hay una librería instalada para procesar archivos {file_ext}.")
                self.add_finding('error', {'message': f'Missing library for {file_ext} files.'})

            # 5. Limpiar el archivo temporal
            os.remove(tmp_file_path)

            if metadata:
                self.add_finding('document_metadata', metadata)
                self.logger.info("[+] Metadatos extraídos con éxito.")
            else:
                self.logger.info("[-] No se encontraron metadatos en el documento.")

        except Exception as e:
            self.logger.error(f"[!] Error durante el análisis de metadatos: {e}")
            self.add_finding('error', {'message': f'An error occurred: {e}'})

        return self.results

    def _extract_pdf_metadata(self, file_path: Path) -> dict:
        """Extrae metadatos de un archivo PDF."""
        try:
            with open(file_path, 'rb') as f:
                reader = PdfReader(f)
                info = reader.metadata
                if info:
                    return {
                        'author': info.get('/Author'),
                        'creator': info.get('/Creator'),
                        'producer': info.get('/Producer'),
                        'creation_date': info.get('/CreationDate'),
                        'modification_date': info.get('/ModDate'),
                        'title': info.get('/Title'),
                    }
        except Exception as e:
            self.logger.error(f"Error reading PDF metadata: {e}")
        return {}

    def _extract_docx_metadata(self, file_path: Path) -> dict:
        """Extrae metadatos de un archivo DOCX."""
        try:
            doc = opendocx(file_path)
            core_props = doc.core_properties
            return {
                'author': core_props.author,
                'created': core_props.created,
                'modified': core_props.modified,
                'last_modified_by': core_props.last_modified_by,
                'title': core_props.title,
                'comments': core_props.comments,
            }
        except Exception as e:
            self.logger.error(f"Error reading DOCX metadata: {e}")
        return {}