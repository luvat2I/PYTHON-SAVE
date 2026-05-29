import requests
from datetime import datetime
import urllib3
from typing import Dict, Optional, Union, List
import csv
import io
import yaml
from dataclasses import dataclass
import os
from pathlib import Path
import re

@dataclass
class SolrConfig:
    """Configuration pour la connexion Solr."""
    server: str
    port: int
    tenant: str
    username: str
    password: str
    verify_ssl: bool = False
    
    @property
    def base_url(self) -> str:
        """Construit l'URL de base pour Solr."""
        return f"https://{self.server}:{self.port}/solr/{self.tenant}/select"

class SolrCsvExporter:
    def __init__(self, config: Union[SolrConfig, str, dict]):
        """
        Initialise l'exporteur CSV pour Solr avec configuration.
        
        Args:
            config: Peut être:
                   - Instance de SolrConfig
                   - Chemin vers un fichier YAML
                   - Dictionnaire de configuration
        """
        if isinstance(config, str):
            self.config = self._load_config_from_file(config)
        elif isinstance(config, dict):
            self.config = SolrConfig(**config)
        elif isinstance(config, SolrConfig):
            self.config = config
        else:
            raise ValueError("Configuration non valide")
        
        if not self.config.verify_ssl:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        self.session = self._create_session()
        
    def _create_session(self) -> requests.Session:
        """Crée une session avec authentification."""
        session = requests.Session()
        session.auth = (self.config.username, self.config.password)
        session.verify = self.config.verify_ssl
        return session
    
    @staticmethod
    def _load_config_from_file(config_path: str) -> SolrConfig:
        """
        Charge la configuration depuis un fichier YAML.
        
        Args:
            config_path: Chemin vers le fichier de configuration
            
        Returns:
            SolrConfig: Configuration chargée
        """
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        return SolrConfig(**config_data)
    
    @staticmethod
    def clean_document_id(document_id: str) -> str:
        """
        Nettoie l'ID du document en supprimant le préfixe.
        
        Args:
            document_id: ID complet du document (ex: XECM-DOCUMENT--PH-DOM5456T.PDF)
            
        Returns:
            str: ID nettoyé (ex: DOM5456T.PDF)
        """
        # Utilise une expression régulière pour extraire l'ID final
        # Pattern pour capturer tout ce qui est à droite du dernier tiret '-'
        match = re.search(r'-([^-]+)$', document_id, re.IGNORECASE)
        if match:
            return match.group(1)
        return document_id  # Retourne l'ID original si le pattern ne correspond pas

    def format_date(self, date_str: str) -> str:
        """
        Formate une date pour Solr.
        
        Args:
            date_str: Date au format YYYYMMDD
            
        Returns:
            str: Date formatée
        """
        try:
            date_obj = datetime.strptime(date_str, '%Y%m%d')
            return date_obj.strftime('%Y%m%d')
        except ValueError:
            raise ValueError("La date doit être au format YYYYMMDD")

    def build_query_params(self, 
                         start_date: str,
                         end_date: str,
                         fields: List[str] = None,
                         rows: int = 10000,
                         nature: Optional[str] = None) -> Dict:
        """
        Construit les paramètres de la requête Solr.
        
        Args:
            start_date: Date de début
            end_date: Date de fin
            fields: Liste des champs à exporter
            rows: Nombre maximum de lignes à retourner
            nature: Nature du document
            
        Returns:
            dict: Paramètres de la requête
        """
        params = {
            'q': 'id:XECM-DOC*',
            'fq': [f'modificationDate:[{self.format_date(start_date)} TO {self.format_date(end_date)}]'],
            'wt': 'csv',
            'rows': rows
        }
        
        if fields:
            params['fl'] = ','.join(fields)
        else:
            params['fl'] = 'id'
            
        if nature:
            params['fq'].append(f'XECM.Document.Keyword.!GNDO_str_en:{nature}')
            
        return params

    def export_to_csv(self,
                     start_date: str,
                     end_date: str,
                     output_file: str,
                     fields: List[str] = None,
                     rows: int = 10000,
                     nature: Optional[str] = None,
                     chunk_size: int = 10000) -> int:
        """
        Exporte les résultats de la requête vers un fichier CSV.
        
        Args:
            start_date: Date de début
            end_date: Date de fin
            output_file: Chemin du fichier de sortie
            fields: Liste des champs à exporter
            rows: Nombre maximum de lignes par requête
            nature: Nature du document
            chunk_size: Taille des blocs pour la pagination
            
        Returns:
            int: Nombre total d'enregistrements exportés
        """
        params = self.build_query_params(
            start_date=start_date,
            end_date=end_date,
            fields=fields,
            rows=chunk_size,
            nature=nature
        )
        
        try:
            # Première requête pour obtenir le total
            params['rows'] = 0
            response = self.session.get(self.config.base_url, params=params)
            response.raise_for_status()
            
            total_records = 0
            
            # Boucle de pagination
            start = 0
            while start < rows:
                params['rows'] = min(chunk_size, rows - start)
                params['start'] = start
                
                response = self.session.get(self.config.base_url, params=params)
                response.raise_for_status()
                
                csv_data = io.StringIO(response.text)
                csv_reader = csv.reader(csv_data)
                
                # Skip header
                next(csv_reader)
                
                # Écriture en mode append (sauf pour le premier chunk)
                mode = 'w' if start == 0 else 'a'
                with open(output_file, mode, newline='', encoding='utf-8') as f:
                    # Traitement direct des IDs sans écrire d'en-tête
                    for row in csv_reader:
                        if row:  # Vérifie que la ligne n'est pas vide
                            clean_id = self.clean_document_id(row[0])
                            f.write(f"{clean_id}\n")
                            total_records += 1
                
                start += chunk_size
                
                if len(response.text.splitlines()) < chunk_size + 1:
                    break
            
            return total_records
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erreur lors de la requête Solr: {str(e)}")
        except IOError as e:
            raise Exception(f"Erreur lors de l'écriture du fichier CSV: {str(e)}")

def extractSolr(server, port, tenant, username, password, start_date, end_date, filePath):
    """
    Exemple d'utilisation avec différentes méthodes de configuration.
    """
    # Exemple de configuration directe
    config = {
        'server': server,
        'port': port,
        'tenant': tenant,
        'username': username,
        'password': password
    }
    
    try:
        exporter = SolrCsvExporter(config)
        
        total_records = exporter.export_to_csv(
            start_date=start_date,
            end_date=end_date,
            output_file=filePath,  # Changed to .txt since it's now one ID per line
            fields=['id'],
            rows=1000000
        )
        print(f"- Fichier de sortie: {filePath}")
        print(f"- Export SOLR terminé avec succès:")
        print(f"- Nombre d'enregistrements SOLR exportés: {total_records}")
        
    except Exception as e:
        print(f"Erreur lors de l'export: {str(e)}")
