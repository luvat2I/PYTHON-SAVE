import requests
import json
import urllib
from urllib.parse import urljoin


class YdgGroupClass: #classe de connexion SGBD SQL et DB2
	def __init__(self, ydg_token,ydg_url, ydg_tenant, ydg_user, ydg_group, ydg_ssl):
		self.ydg_token = ydg_token
		self.ydg_url = ydg_url
        self.ydg_tenant = ydg_tenant
        self.ydg_user = ydg_user
        self.ydg_group = ydg_group
        self.ydg_ssl = ydg_ssl
        
    def ydg_group_lecture(self,group_lecture):
		headers = {"Authorization": f"Bearer {TOKEN}"}
        service_context_obj = {
            "userId": self.ydg_user,
            "environmentName": self.ydg_tenant,
            "regionalSettings": "fr",
            "contextualRole": ""
        }
        SERVICE_CONTEXT = urllib.parse.quote(json.dumps(service_context_obj, separators=(",", ":")), safe='')
        check_url = f"{self.ydg_url}/xframework-security-web/rest/group/{group_lecture}?serviceContext={SERVICE_CONTEXT}"
        check_resp = requests.get(check_url, headers=headers, verify=False, timeout=30)
        check_text = check_resp.text
        return check_text