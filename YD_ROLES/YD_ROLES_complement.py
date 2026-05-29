import configparser
import os
import sys

def get_INFO_CONFIG(CONFIG_INI,VALEUR1,VALEUR2) :
	try:
		RETURN = CONFIG_INI[f"{VALEUR1}"][f"{VALEUR2}"]
	except Exception as e:
		RETURN = "ERROR"
	return RETURN

def get_BOOL_CONFIG(CONFIG_INI,VALEUR1,VALEUR2) :
	try:
		RETURN = CONFIG_INI.getboolean(f"{VALEUR1}", f"{VALEUR2}")
	except Exception as e:
		RETURN = "ERROR"
	return RETURN