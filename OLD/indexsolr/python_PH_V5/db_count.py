import pyodbc
import csv
from datetime import datetime

def format_date_for_query(date_str):
    """
    Convertit une date au format 'YYYYMMDD' en format compatible avec la base de données.
    
    Args:
        date_str (str): Date au format 'YYYYMMDD'
    
    Returns:
        str: Date formatée pour la requête
    """
    try:
        # Vérifie si la date est au bon format
        datetime.strptime(date_str, '%Y%m%d')
        return date_str
    except ValueError:
        raise ValueError("La date doit être au format 'YYYYMMDD'")

def get_count_by_date_range(cursor, start_date, end_date):
    """
    Compte les enregistrements dans une plage de dates.
    
    Args:
        cursor: Curseur de base de données
        start_date (str): Date de début au format 'YYYYMMDD'
        end_date (str): Date de fin au format 'YYYYMMDD'
    
    Returns:
        int: Nombre d'enregistrements trouvés
    """

    query = """
        SELECT COUNT(*) 
        FROM YDOCDTAPH.ARG0CPP 
        WHERE DDR67A BETWEEN ? AND ?
    """
    
    cursor.execute(query, (start_date, end_date))
    return cursor.fetchone()[0]

def get_countIndex_by_date_range(cursor, start_date, end_date):
    """
    Compte les enregistrements dans une plage de dates.
    
    Args:
        cursor: Curseur de base de données
        start_date (str): Date de début au format 'YYYYMMDD'
        end_date (str): Date de fin au format 'YYYYMMDD'
    
    Returns:
        int: Nombre d'enregistrements trouvés
    """

    query = """
        SELECT COUNT(*) 
        FROM YDOCDTAPH.ARG0CPP 
        WHERE DDr67A BETWEEN ? AND ?
    """
    
    cursor.execute(query, (start_date, end_date))
    return cursor.fetchone()[0]

def get_itemToIndex_by_date_range(cursor, start_date, end_date):
    """
    Récupère les enregistrements ddepuis une plage de dates.
    
    Args:
        cursor: Curseur de base de données
        start_date (str): Date de début au format 'YYYYMMDD'
        end_date (str): Date de fin au format 'YYYYMMDD'
    
    Returns:
        int: Nombre d'enregistrements trouvés
    """

    query = """
        SELECT DD1rA 
        FROM YDOCDTAPH.ARG0CPP 
        WHERE DDr67A BETWEEN ? AND ?
    """
    
    cursor.execute(query, (start_date, end_date))
    
    return cursor.fetchall()
    
def get_count_by_date_range_and_nature(server, db_type, database, port, username, password, start_date, end_date, filePath):
    """
    Compte les enregistrements dans une plage de dates pour une nature spécifique.
    
    Args:
        start_date (str): Date de début au format 'YYYYMMDD'
        end_date (str): Date de fin au format 'YYYYMMDD'
        nature_prefix (str): Préfixe de la nature (par défaut 'FACFOU')
    
    Returns:
        int: Nombre d'enregistrements trouvés
    """
    # Connexion à la base de données en fonction du type (SQL ou DB2)
    if db_type == 'DB2':
        conn_str = f'DRIVER={{iSeries access ODBC Driver}};SYSTEM={server};PORT={port};DATABASE={database};PROTOCOL=TCPIP;UID={username};PWD={password}'
    else:
        conn_str = f'DRIVER={{SQL Server}};SERVER={server};PORT={port};DATABASE={database};UID={username};PWD={password};Trusted_Connection=No;'
    
    try:
        # Establish connection
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        start_formatted = format_date_for_query(start_date)
        end_formatted = format_date_for_query(end_date)
        
        if (db_type == 'DB2'):
            start_formatted = f"{start_formatted[:4]}-{start_formatted[4:6]}-{start_formatted[6:]}"
            end_formatted = f"{end_formatted[:4]}-{end_formatted[4:6]}-{end_formatted[6:]}"

        # Pour compter tous les enregistrements entre 2 dates
        count_all = get_count_by_date_range(cursor, "1" + start_date[2:], "1" + end_date[2:])
        print(f"Nombre total d'enregistrements ARAPREP: {count_all}")
        # Pour compter tous les enregistrements dans la table d'indexation entre 2 dates
        count_index = get_countIndex_by_date_range(cursor, start_formatted, end_formatted)
        print(f"Nombre total d'enregistrements indexés ARG0CPP: {count_index}")
        # Pour écrire tous les enregistrements dans un fichier type csv
        indexID = get_itemToIndex_by_date_range(cursor, start_formatted, end_formatted)
        m_dict = list(indexID)

        with open(filePath, "w", newline='', encoding='UTF-8') as f:
            w = csv.writer(f)
    
            # Écrire les clés (entêtes) si c'est un dictionnaire
            if isinstance(m_dict, dict):
                w.writerow(m_dict.keys())
    
            # Si c'est un ensemble de résultats de pyodbc
            for row in m_dict:
                # Convertir chaque champ en chaîne de caractères si nécessaire
                w.writerow([str(x) for x in row])
            
            f.close()

    except pyodbc.Error as e:
        print(f"Database error: {str(e)}")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()


