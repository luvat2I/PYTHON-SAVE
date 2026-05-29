import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

class GestionnaireLogFile:
    """Classe pour gérer l'enregistrement des logs dans un dossier (sans affichage console)"""
    
    def __init__(self, nom_dossier="logs", nom_fichier="app.log", 
                 niveau=logging.DEBUG, max_bytes=1024*1024, backup_count=5):
        """
        Initialise le gestionnaire de logs
        
        Args:
            nom_dossier (str): Chemin du dossier pour les logs
            nom_fichier (str): Nom du fichier de log
            niveau (int): Niveau de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            max_bytes (int): Taille maximale d'un fichier en bytes (par défaut 1 Mo)
            backup_count (int): Nombre de fichiers de sauvegarde à conserver
        """
        self.nom_dossier = nom_dossier
        self.nom_fichier = nom_fichier
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(niveau)
        
        # Créer le dossier s'il n'existe pas
        if not os.path.exists(nom_dossier):
            os.makedirs(nom_dossier)
        
        # Chemin complet du fichier
        chemin_fichier = os.path.join(nom_dossier, nom_fichier)
        
        # Gestionnaire avec rotation (FICHIER UNIQUEMENT)
        file_handler = RotatingFileHandler(
            chemin_fichier,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(niveau)
        
        # Format des logs
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # Ajouter uniquement le gestionnaire fichier (pas de console)
        self.logger.addHandler(file_handler)
    
    def debug(self, message):
        """Enregistrer un message de debug"""
        self.logger.debug(message)
    
    def info(self, message):
        """Enregistrer un message informatif"""
        self.logger.info(message)
    
    def warning(self, message):
        """Enregistrer un avertissement"""
        self.logger.warning(message)
    
    def error(self, message):
        """Enregistrer une erreur"""
        self.logger.error(message)
    
    def critical(self, message):
        """Enregistrer un message critique"""
        self.logger.critical(message)
