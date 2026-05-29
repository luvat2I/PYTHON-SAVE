import requests
import json
import urllib
from urllib.parse import urljoin

def ydg_group_lecture(TOKEN,
						YDG_BASE, TENANT,
						USER_ID,
						GROUP,
						VERIF_SSL):
	#client_user.client_user(TYPEACTION,token_gestion_access_token,KEYCLOAK_BASE, REALM, VERIF_SSL)
	error = False
	ID_APP = "YG001"
	
	#headers
	if not error :
		try:
			headers = {
				"Authorization": f"Bearer {TOKEN}"
			}
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "0002",
				"message": f"{e}",
				"message2": ""
			}
			error = True
			
	#service_context_obj
	if not error :
		try:
			service_context_obj = {
				"userId": USER_ID,
				"environmentName": TENANT,
				"regionalSettings": "fr",
				"contextualRole": ""
			}
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "0002",
				"message": f"{e}",
				"message2": ""
			}
			error = True
	
	#SERVICE_CONTEXT
	if not error :
		try:
			SERVICE_CONTEXT = urllib.parse.quote(json.dumps(service_context_obj, separators=(",", ":")), safe='')
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "0003",
				"message": f"{e}",
				"message2": ""
			}
			error = True
	
	#check_url
	if not error :
		try:
			check_url = f"{YDG_BASE}/xframework-security-web/rest/group/001-adm-grp?serviceContext={SERVICE_CONTEXT}"
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "0004",
				"message": f"{e}",
				"message2": ""
			}
			error = True
	
	#check_resp
	if not error :
		try:
			check_resp = requests.get(check_url, headers=headers, verify=False, timeout=30)
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "0004",
				"message": f"{e}",
				"message2": ""
			}
			error = True
			
	#check_text
	if not error :
		try:
			check_text = check_resp.text
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "0005",
				"message": f"{e}",
				"message2": ""
			}
			error = True
	#check_text
	if not error :
		try:
			return {
				"code": ID_APP,
				"result": check_text,
				"error": "",
				"message": f"group : {check_text}",
				"message2": ""
			}
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "0006",
				"message": f"{e}",
				"message2": ""
			}
			error = True


def ydg_group_creation(TOKEN,
						YDG_BASE, TENANT,
						USER_ID,
						GROUP,
						VERIF_SSL):
	error = False
	ID_APP = "YG002"
	
	headers = {
				"Authorization": f"Bearer {TOKEN}"
			}
	
	service_context_obj = {
				"userId": USER_ID,
				"environmentName": TENANT,
				"regionalSettings": "fr",
				"contextualRole": ""
			}
	
	SERVICE_CONTEXT = urllib.parse.quote(json.dumps(service_context_obj, separators=(",", ":")), safe='')
	
	Contenu =  {
			"users": [],
			"securityClasses": [],
			"group": {
				"name": "groupeTest3",
				"displayName": "groupeTest34"
			}
		}
	payload = {"name":"Nouveau groupe","displayName":"test"}
	check_url = f"{YDG_BASE}/xframework-saas-web/rest/group/with-users-and-classes?serviceContext={SERVICE_CONTEXT}"
	params = {"serviceContext": json.dumps({"userId":"lainxluva","environmentName":"001","regionalSettings":"fr","contextualRole":""})}
	print(check_url)
	check_resp = requests.post(check_url, headers=headers,params=params,json=payload, verify=False, timeout=30)
	check_text = check_resp.text
	print(check_text)
	
	
	

def ydg_group_creation2(TOKEN,
						YDG_BASE, TENANT,
						USER_ID,
						GROUP,
						VERIF_SSL):
	error = False
	ID_APP = "YG002"
	
	headers = {
				"Authorization": f"Bearer {TOKEN}"
			}
	
	service_context_obj = {
				"userId": USER_ID,
				"environmentName": TENANT,
				"regionalSettings": "fr",
				"contextualRole": ""
			}
	
	SERVICE_CONTEXT = urllib.parse.quote(json.dumps(service_context_obj, separators=(",", ":")), safe='')
	
	
	check_url = f"{YDG_BASE}/xframework-security-web/rest/group/testpourvoir?serviceContext={SERVICE_CONTEXT}"
	
	print(check_url)
	check_resp = requests.put(check_url, headers=headers, verify=False, timeout=30)
	check_text = check_resp.text
	print(check_text)