"""
Sistema de logging para o projeto TRI
"""
import logging
import logging.handlers
from pathlib import Path
from typing import Optional
from config.settings import LOGGING_CONFIG


class TRILogger:
    """Logger personalizado para o sistema TRI"""
    
    def __init__(self, name: str = "tri_system", level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Evitar duplicação de handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Configura os handlers do logger"""
        # Handler para arquivo com rotação
        file_handler = logging.handlers.RotatingFileHandler(
            LOGGING_CONFIG["file"],
            maxBytes=LOGGING_CONFIG["max_size"],
            backupCount=LOGGING_CONFIG["backup_count"],
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Handler para console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(LOGGING_CONFIG["format"])
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Adicionar handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def debug(self, message: str):
        """Log de debug"""
        self.logger.debug(message)
    
    def info(self, message: str):
        """Log de informação"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log de aviso"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log de erro"""
        self.logger.error(message)
    
    def critical(self, message: str):
        """Log crítico"""
        self.logger.critical(message)
    
    def log_processing_start(self, file_path: str, num_students: int, num_items: int):
        """Log do início do processamento"""
        self.info(f"Iniciando processamento: {file_path}")
        self.info(f"Estudantes: {num_students}, Itens: {num_items}")
    
    def log_processing_end(self, duration: float, output_file: str):
        """Log do fim do processamento"""
        self.info(f"Processamento concluído em {duration:.2f}s")
        self.info(f"Arquivo de saída: {output_file}")
    
    def log_validation_error(self, error: str):
        """Log de erro de validação"""
        self.error(f"Erro de validação: {error}")
    
    def log_tri_estimation(self, student_id: str, theta: float, enem_score: float):
        """Log da estimação TRI para um estudante"""
        self.debug(f"Estudante {student_id}: theta={theta:.3f}, ENEM={enem_score:.0f}")


# Logger global
logger = TRILogger()


def get_logger(name: str = "tri_system") -> TRILogger:
    """Retorna uma instância do logger"""
    return TRILogger(name)
