import os
import shutil
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import configparser
import time
import logging
from datetime import datetime, timedelta  # Assurez-vous d'importer timedelta
import threading
import win32serviceutil
import win32service
import win32event
import servicemanager

class youdoc_flatten(win32serviceutil.ServiceFramework):
    _svc_name_ = "youdoc_flatten"
    _svc_display_name_ = "youdoc_flatten Python"
    _svc_description_ = "Un service Windows qui écrit dans un fichier log toutes les minutes."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.running = True
        self.source_folder, self.traitement_folder, self.export_folder, self.enable_archive, self.archive_folder, self.fic_type, self.enable_logging, self.log_folder  = self.read_config()  # Lire les dossiers de log
           
    def read_config(self):
        """Lit les chemins des dossiers de log depuis le fichier de configuration."""
        config = configparser.ConfigParser()
        config.read('config.ini')
        source_folder = config['folders']['source_folder']
        traitement_folder = config['folders']['traitement_folder']
        export_folder = config['folders']['export_folder']
        enable_archive = config.getboolean('archives', 'enable_archive')
        archive_folder = config['archives']['archive_folder']
        fic_type = config['files']['fic_type']
        enable_logging = config.getboolean('logging', 'enable_logging')
        log_folder = config['logging']['log_folder']
        return source_folder, traitement_folder, export_folder, enable_archive, archive_folder, fic_type, enable_logging, log_folder

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
            if not os.path.exists(self.log_folder):
                os.makedirs(self.log_folder)  # Crée le dossier s'il n'existe pas
            
            if self.enable_logging:
                logging.info(f"{self.fic_type} Log entry at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            time.sleep(60)  # Attendre une minute


if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(youdoc_flatten)
