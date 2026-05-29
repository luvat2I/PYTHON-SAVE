import configparser
import os
import sys

import time
from datetime import datetime, timedelta, timezone
from datetime import date

import win32evtlogutil
import win32evtlog
import win32api
import win32con

def get_ini_path():
    script_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    return os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), f"{script_name}.ini")

def get_nom_programme():
	return os.path.splitext(os.path.basename(sys.argv[0]))[0]

def nom_programme_contient(NOM_PROGRAMME,TERME) :
	return TERME.lower() in NOM_PROGRAMME.lower()
	
def log_service(LOG_LEVEL,LOG_TEXT,LOG_EVENT_LEVEL,LOGGER_SERVICE):
	if LOG_LEVEL == "DEBUG" and LOG_EVENT_LEVEL == "DEBUG" :
		LOGGER_SERVICE.debug(f"{LOG_TEXT}")
	if LOG_LEVEL == "INFO" and (LOG_EVENT_LEVEL == "DEBUG" or LOG_EVENT_LEVEL == "INFO") :
		LOGGER_SERVICE.info(f"{LOG_TEXT}")
	elif LOG_LEVEL == "WARNING" and (LOG_EVENT_LEVEL == "DEBUG" or LOG_EVENT_LEVEL == "INFO" or LOG_EVENT_LEVEL == "WARNING"):
		LOGGER_SERVICE.warning(f"{LOG_TEXT}")
	elif LOG_LEVEL == "ERROR" :
		LOGGER_SERVICE.error(f"{LOG_TEXT}")
		
def log_console(LOG_LEVEL,LOG_TEXT,LOG_CONSOLE_LEVEL,TRAITEMENT_TYPE):
	if TRAITEMENT_TYPE == "exe" :
		current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		if LOG_LEVEL == "DEBUG" and LOG_CONSOLE_LEVEL == "DEBUG" :
			print(f"{current_time} > {LOG_LEVEL} > {LOG_TEXT}")
		if LOG_LEVEL == "INFO" and (LOG_CONSOLE_LEVEL == "DEBUG" or LOG_CONSOLE_LEVEL == "INFO") :
			print(f"{current_time} > {LOG_LEVEL} > {LOG_TEXT}")
		elif LOG_LEVEL == "WARNING" and (LOG_CONSOLE_LEVEL == "DEBUG" or LOG_CONSOLE_LEVEL == "INFO" or LOG_CONSOLE_LEVEL == "WARNING"):
			print(f"{current_time} > {LOG_LEVEL} > {LOG_TEXT}")
		elif LOG_LEVEL == "ERROR" :
			print(f"{current_time} > {LOG_LEVEL} > {LOG_TEXT}")

def log_secure(LOG_TYPE,LOG_LEVEL,LOG_TEXT,LOG_EVENT_LEVEL,LOGGER_SERVICE,LOG_CONSOLE_LEVEL,TRAITEMENT_TYPE):
	if LOG_TYPE == "0" :
		log_service(LOG_LEVEL,LOG_TEXT,LOG_EVENT_LEVEL,LOGGER_SERVICE) 
	log_console(LOG_LEVEL,LOG_TEXT,LOG_CONSOLE_LEVEL,TRAITEMENT_TYPE)
	if TRAITEMENT_TYPE == "exe" and LOG_LEVEL == "ERROR" :
		input("Appuyez sur une touche pour quitter...")
		
### création d'une source d'événements si elle n'existe pas pour le mode service ###
def create_event_source(SOURCE_NAME):
	try:
		win32evtlogutil.ReportEvent(SOURCE_NAME, 1, eventType=win32evtlog.EVENTLOG_INFORMATION_TYPE, strings=[SOURCE_NAME])
	except Exception as e:
		print("error")
		win32api.RegCreateKey(win32con.HKEY_LOCAL_MACHINE, f'SYSTEM\\CurrentControlSet\\Services\\EventLog\\Application\\{SOURCE_NAME}')
		win32api.RegSetValue(win32api.RegOpenKey(win32con.HKEY_LOCAL_MACHINE, f'SYSTEM\\CurrentControlSet\\Services\\EventLog\\Application\\{SOURCE_NAME}'), 'EventMessageFile', win32con.REG_SZ, os.path.abspath(__file__))
		win32api.RegSetValue(win32api.RegOpenKey(win32con.HKEY_LOCAL_MACHINE, f'SYSTEM\\CurrentControlSet\\Services\\EventLog\\Application\\{SOURCE_NAME}'), 'TypesSupported', win32con.REG_DWORD, 7)
		
def log_enreg(LOG_LEVEL,LOG_TEXT,LOGGER_FOLDER):
	current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	if LOG_LEVEL == "DEBUG" and log_folder_level == "DEBUG" :
		LOGGER_FOLDER.debug(f"{LOG_TEXT}")
	if LOG_LEVEL == "INFO" and (log_folder_level == "DEBUG" or log_folder_level == "INFO") :
		LOGGER_FOLDER.info(f"{LOG_TEXT}")
	elif LOG_LEVEL == "WARNING" and (log_folder_level == "DEBUG" or log_folder_level == "INFO" or log_folder_level == "WARNING"):
		LOGGER_FOLDER.warning(f"{LOG_TEXT}")
	elif LOG_LEVEL == "ERROR" :
		LOGGER_FOLDER.error(f"{LOG_TEXT}")

def log_event(LOG_TYPE,LOG_LEVEL,LOG_TEXT,LOG_EVENT_LEVEL,LOG_CONSOLE_LEVEL,LOGGER_FOLDER,LOGGER_SERVICE,TRAITEMENT_TYPE):
	if LOG_TYPE == "0" :
		if enable_logging :
			log_enreg(LOG_LEVEL,LOG_TEXT,LOGGER_FOLDER)
		log_service(LOG_LEVEL,LOG_TEXT,LOG_EVENT_LEVEL,LOGGER_SERVICE)
		log_console(LOG_LEVEL,LOG_TEXT,LOG_CONSOLE_LEVEL,TRAITEMENT_TYPE)
	elif LOG_TYPE == "1" :
		if enable_logging :
			log_enreg(LOG_LEVEL,LOG_TEXT,LOGGER_FOLDER)
		log_console(LOG_LEVEL,LOG_TEXT,LOG_CONSOLE_LEVEL,TRAITEMENT_TYPE)
	elif LOG_TYPE == "2" :
		log_console(LOG_LEVEL,LOG_TEXT,LOG_CONSOLE_LEVEL,TRAITEMENT_TYPE)
		
def get_enable_logging(LOG_VALIDATION,CONFIG_INI):
	try:
		if LOG_VALIDATION :
			enable_logging = CONFIG_INI.getboolean('logging', 'enable_logging')
		else :
			enable_logging = False
	except Exception as e:
		enable_logging = False	
	return enable_logging
		
def get_licence(CONFIG_INI) :
	try:
		LICENCE_CODE = CONFIG_INI['LICENCE']['LICENCE']
	except Exception as e:
		LICENCE_CODE = "ERROR"
	return LICENCE_CODE







def get_param(CONFIG_INI,PARAM1,PARAM2) :
    try:
        PARAM = CONFIG_INI[f'{PARAM1}'][f'{PARAM2}']
        return {
                "error": False,
                "return": PARAM
                }
    except Exception as e:
        return {
                "error": True,
                "return": f"ERROR : {e}"
                }
def get_bool_param(CONFIG_INI,PARAM1,PARAM2) :
    try:
        PARAM = CONFIG_INI.getboolean(f'{PARAM1}', f'{PARAM2}')
        return {
                "error": False,
                "return": PARAM
                }
    except Exception as e:
        return {
                "error": True,
                "return": f"ERROR : {e}"
                }


		