"""
Sistema de logging centralizado para el backend de SARA.
Captura toda la salida de consola con fecha y hora.
"""

import sys
import os
from datetime import datetime
from pathlib import Path


class Logger:
    """Logger personalizado que captura stdout y stderr con timestamps."""
    
    def __init__(self, log_dir="logs", log_file_prefix="sara_backend"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Crear archivo de log con fecha
        timestamp = datetime.now().strftime("%Y%m%d")
        self.log_file = self.log_dir / f"{log_file_prefix}_{timestamp}.log"
        
        # Guardar los streams originales
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
        # Inicializar el logger
        self._setup_logging()
    
    def _get_timestamp(self):
        """Genera timestamp con fecha y hora."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    
    def _write_log(self, message, stream_type="INFO"):
        """Escribe un mensaje al archivo de log con timestamp."""
        timestamp = self._get_timestamp()
        log_line = f"[{timestamp}] [{stream_type}] {message}\n"
        
        # Escribir al archivo
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_line)
        except Exception as e:
            # Si falla escribir al archivo, al menos imprimir al stream original
            self.original_stdout.write(f"Error writing to log: {e}\n")
    
    def _create_stream_wrapper(self, original_stream, stream_type):
        """Crea un wrapper que intercepta la salida del stream."""
        class StreamWrapper:
            def __init__(self, logger_instance, orig_stream, type_name):
                self.logger = logger_instance
                self.orig_stream = orig_stream
                self.type_name = type_name
                self.buffer = ""
            
            def write(self, text):
                # Escribir al stream original
                self.orig_stream.write(text)
                
                # Acumular en buffer para líneas completas
                self.buffer += text
                
                # Procesar líneas completas
                while '\n' in self.buffer:
                    line, self.buffer = self.buffer.split('\n', 1)
                    if line:  # Solo loggear si hay contenido
                        self.logger._write_log(line, self.type_name)
                
                # Forzar flush del stream original
                self.orig_stream.flush()
            
            def flush(self):
                # Procesar cualquier contenido restante en el buffer
                if self.buffer:
                    self.logger._write_log(self.buffer, self.type_name)
                    self.buffer = ""
                self.orig_stream.flush()
        
        return StreamWrapper(self, original_stream, stream_type)
    
    def _setup_logging(self):
        """Configura el sistema de logging interceptando stdout y stderr."""
        # Crear wrappers para stdout y stderr
        sys.stdout = self._create_stream_wrapper(self.original_stdout, "STDOUT")
        sys.stderr = self._create_stream_wrapper(self.original_stderr, "STDERR")
        
        # Log inicial
        self._write_log("=" * 80, "INFO")
        self._write_log("Logger inicializado. Capturando stdout y stderr.", "INFO")
        self._write_log(f"Archivo de log: {self.log_file}", "INFO")
        self._write_log("=" * 80, "INFO")
    
    def info(self, message):
        """Log un mensaje de info explícito."""
        self._write_log(message, "INFO")
    
    def error(self, message):
        """Log un mensaje de error explícito."""
        self._write_log(message, "ERROR")
    
    def warning(self, message):
        """Log un mensaje de advertencia explícito."""
        self._write_log(message, "WARNING")
    
    def debug(self, message):
        """Log un mensaje de debug explícito."""
        self._write_log(message, "DEBUG")
    
    def restore_original_streams(self):
        """Restaura los streams originales de stdout y stderr."""
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        self._write_log("Streams originales restaurados.", "INFO")


# Instancia global del logger
_logger_instance = None


def init_logger(log_dir="logs", log_file_prefix="sara_backend"):
    """Inicializa el logger global."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = Logger(log_dir, log_file_prefix)
    return _logger_instance


def get_logger():
    """Obtiene la instancia del logger global."""
    return _logger_instance


def log(message, level="INFO"):
    """Función conveniente para loggear mensajes."""
    if _logger_instance:
        _logger_instance._write_log(message, level)
