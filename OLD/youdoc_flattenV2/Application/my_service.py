import os
import time
import configparser
import win32serviceutil
import win32service
import win32event
import servicemanager
import logging

class MyService(win32serviceutil.ServiceFramework):
    _svc_name_ = "MyPythonService"
    _svc_display_name_ = "My Python Service"
    _svc_description_ = "Un service Windows qui exécute une tâche périodique."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.running = True
        self.log_folder = "D:\\PYTHON\\youdoc_flattenV2\\Tests\\logs"  # Changez ce chemin
        self.setup_logging()

    def setup_logging(self):
        if not os.path.exists(self.log_folder):
            os.makedirs(self.log_folder)
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
            logging.info("Service is running at %s", time.strftime('%Y-%m-%d %H:%M:%S'))
            time.sleep(60)  # Attendre une minute

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(MyService)
