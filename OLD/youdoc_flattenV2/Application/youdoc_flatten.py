import os
import time
import configparser
import win32serviceutil
import win32service
import win32event
import servicemanager
import logging

class youdoc_flatten(win32serviceutil.ServiceFramework):
    _svc_name_ = "youdoc_flatten"
    _svc_display_name_ = "youdoc_flatten"
    _svc_description_ = "Un service youdoc_flatten."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.running = True
        
        # Lire le fichier de configuration
        self.config_file_path = 'D:\PYTHON\youdoc_flattenV2\Application\config.ini'  # Chemin vers votre fichier INI
        self.read_config()

        # Configuration du logging
        self.setup_logging()

    def read_config(self):
        """Lit les chemins des dossiers depuis le fichier de configuration."""
        if os.path.exists(self.config_file_path):
            config = configparser.ConfigParser()
            config.read(self.config_file_path)

            # Récupération des informations
            self.source_folder = config['folders']['source_folder']
            self.traitement_folder = config['folders']['traitement_folder']
            self.export_folder = config['folders']['export_folder']
            
            self.enable_archive = config.getboolean('archives', 'enable_archive')
            self.archive_folder = config['archives']['archive_folder']
            
            self.fic_type = config['files']['fic_type']
            
            self.enable_logging = config.getboolean('logging', 'enable_logging')
            self.log_folder = config['logging']['log_folder']
        else:
            raise FileNotFoundError(f"Le fichier {self.config_file_path} n'existe pas.")

    def setup_logging(self):
        """Configure le logging pour le service."""
        if not os.path.exists(self.log_folder):
            os.makedirs(self.log_folder)  # Crée le dossier s'il n'existe pas
        logging.basicConfig(filename=os.path.join(self.log_folder, 'service.log'), level=logging.INFO)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.running = False

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                               servicemanager.PYS_SERVICE_STARTED,
                               (self._svc_name_, ''))
        self.main()

    def main(self):
        while self.running:
            if self.enable_logging:
                logging.info("Service is running at %s", time.strftime('%Y-%m-%d %H:%M:%S'))
            time.sleep(60)  # Attendre une minute

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(youdoc_flatten)
