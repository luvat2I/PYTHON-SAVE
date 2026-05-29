from enum import Enum
from datetime import datetime

class LogLevel(Enum):
    DEBUG = 1
    INFO = 2
    WARNING = 3
    ERROR = 4
    CRITICAL = 5
    DISABLED = 6

class Logger:
    def __init__(self, level=LogLevel.INFO):
        """
        Initialise le logger.
        
        Args:
            level (LogLevel): Le niveau de log minimum à afficher. Par défaut INFO.
            name (str): Le nom du logger pour identifier la source des logs.
        """
        self.level = level
    
    def _log(self, message, log_level):
        """
        Enregistre un message si le niveau est activé et >= au niveau minimum.
        
        Args:
            message (str): Le message à afficher.
            log_level (LogLevel): Le niveau de ce message.
        """
        if self.level == LogLevel.DISABLED or log_level.value < self.level.value:
            return
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{timestamp} - {log_level.name} - {message}")
    
    def debug(self, message):
        """Enregistre un message de niveau DEBUG."""
        self._log(message, LogLevel.DEBUG)
    
    def info(self, message):
        """Enregistre un message de niveau INFO."""
        self._log(message, LogLevel.INFO)
    
    def warning(self, message):
        """Enregistre un message de niveau WARNING."""
        self._log(message, LogLevel.WARNING)
    
    def error(self, message):
        """Enregistre un message de niveau ERROR."""
        self._log(message, LogLevel.ERROR)
    
    def critical(self, message):
        """Enregistre un message de niveau CRITICAL."""
        self._log(message, LogLevel.CRITICAL)
        
    def vide(self):
        """fait un message vide"""
        print(f"")
