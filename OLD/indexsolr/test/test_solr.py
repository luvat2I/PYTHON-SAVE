import pysolr
import requests
from requests.auth import HTTPBasicAuth
import urllib3
import json
import re
# Désactiver les avertissements de sécurité pour les requêtes non vérifiées
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SolrClient:
    def __init__(self, solr_url, username, password):
        self.solr_url = solr_url
        self.username = username
        self.password = password

    def search(self, query, rows=10):
        # Effectuer la recherche dans Solr avec désactivation de la vérification SSL
        response = requests.get(
            f"{self.solr_url}/select",
            params={'q': query, 'rows': rows},
            auth=HTTPBasicAuth(self.username, self.password),
            verify=False  # Désactiver la vérification SSL
        )
        response.raise_for_status()  # Vérifier si la requête a réussi
        return response.json()['response']['docs']

    def display_results(self, results):
        # Afficher les résultats
        print(f"Nombre de résultats: {len(results)}")
        for result in results:
            clean_id = self.clean_document_id(f"{result['id']}")
            print(f"{clean_id}")
            print(f"{result.get('processTimeStamp', 'N/A')}")

    def clean_document_id(self, document_id: str) -> str:
        match = re.search(r'-([^-]+)$', document_id, re.IGNORECASE)
        if match:
            return match.group(1)
        return document_id  # Retourne l'ID original si le pattern ne correspond pas
# Exemple d'utilisation
if __name__ == "__main__":
    solr_url = 'https://ydgluva2022:8984/solr/001'  # Remplacez par l'URL de votre serveur Solr
    username = 'prd-dft-svc'  # Remplacez par votre nom d'utilisateur
    password = 'prddftsvcT2I'  # Remplacez par votre mot de passe

    client = SolrClient(solr_url, username, password)

    query = 'id:[XECM-FOLDER--001-00000 TO *] AND id:*FOLD*'  # Remplacez par votre requête de recherche
    results = client.search(query)
    client.display_results(results)
