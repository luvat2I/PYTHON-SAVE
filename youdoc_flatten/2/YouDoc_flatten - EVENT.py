import logging
import logging.handlers
import os

# Créer une source d'événements si elle n'existe pas
def create_event_source():
    import win32evtlogutil
    import win32evtlog
    import win32api
    import win32con

    # Nom de la source
    source_name = 'TEST'
    # Nom de l'application
    app_name = 'TEST'

    # Vérifier si la source existe déjà
    try:
        win32evtlogutil.ReportEvent(source_name, 1, eventType=win32evtlog.EVENTLOG_INFORMATION_TYPE, strings=[app_name])
    except Exception as e:
        # Créer la source si elle n'existe pas
        win32api.RegCreateKey(win32con.HKEY_LOCAL_MACHINE, f'SYSTEM\\CurrentControlSet\\Services\\EventLog\\Application\\{source_name}')
        win32api.RegSetValue(win32api.RegOpenKey(win32con.HKEY_LOCAL_MACHINE, f'SYSTEM\\CurrentControlSet\\Services\\EventLog\\Application\\{source_name}'), 'EventMessageFile', win32con.REG_SZ, os.path.abspath(__file__))
        win32api.RegSetValue(win32api.RegOpenKey(win32con.HKEY_LOCAL_MACHINE, f'SYSTEM\\CurrentControlSet\\Services\\EventLog\\Application\\{source_name}'), 'TypesSupported', win32con.REG_DWORD, 7)

# Configuration du logger
logger = logging.getLogger('TEST')
logger.setLevel(logging.INFO)

# Handler pour écrire dans le journal des événements Windows
handler = logging.handlers.NTEventLogHandler('TEST')
logger.addHandler(handler)

def main():
    create_event_source()  # Créer la source d'événements
    while True:
        logger.info('Mon service fonctionne...')
        time.sleep(60)  # Attendre 60 secondes

if __name__ == '__main__':
    main()
