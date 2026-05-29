import configparser
import os
import sys

def get_TENANT(CONFIG_INI) :
	try:
		TENANT = CONFIG_INI['ENTRA_ID']['TENANT']
	except Exception as e:
		TENANT = "ERROR"
	return TENANT

def get_CLIENT_ID(CONFIG_INI) :
	try:
		CLIENT_ID = CONFIG_INI['ENTRA_ID']['CLIENT_ID']
	except Exception as e:
		CLIENT_ID = "ERROR"
	return CLIENT_ID

def get_CLIENT_SECRET(CONFIG_INI) :
	try:
		CLIENT_SECRET = CONFIG_INI['ENTRA_ID']['CLIENT_SECRET']
	except Exception as e:
		CLIENT_SECRET = "ERROR"
	return CLIENT_SECRET


def get_token_path():
    script_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    return os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), f"{script_name}.token")

def get_id_token_path():
    script_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    return os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), f"{script_name}.id_token")
	
def get_access_token_path():
    script_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    return os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), f"{script_name}.access_token")