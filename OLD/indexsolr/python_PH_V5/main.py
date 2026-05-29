#pyinstaller --onefile --console --name reindex_PH main.py
import remove_duplicates
import db_count
import update_sql
import solr_export
import argparse
from datetime import datetime, date

def validate_date(date_str):
    try:
        datetime.strptime(date_str, '%Y%m%d')
        return date_str
    except ValueError:
        raise argparse.ArgumentTypeError(f"Date invalide: {date_str}. Utilisez le format YYYYMMDD")

def main():
    # Configuration du parser d'arguments
    parser = argparse.ArgumentParser(description='Réindexation des documents')
    parser.add_argument('start_date', type=validate_date, help='Date de début au format YYYYMMDD')
    parser.add_argument('--end_date', type=validate_date, 
                      help='Date de fin au format YYYYMMDD (date du jour par défaut)')

    # Parse les arguments
    args = parser.parse_args()

    # Si end_date n'est pas spécifiée, utiliser la date du jour
    if not args.end_date:
        args.end_date = datetime.now().strftime('%Y%m%d')

    # On compte et on extrait les documents indexés en BDD
    db_count.get_count_by_date_range_and_nature( 
        server='o75PRD',
        db_type='DB2',
        username='YDOCADM',
        password='T9S7UHT545',
        database='YDOCDTAPH',
        port='446',  # Default port for DB2 Server, change if different
        start_date=args.start_date,
        end_date=args.end_date,
        filePath='resultat_sgbd.txt'
    )

    # On extrait les documents indexés dans SOLR
    solr_export.extractSolr(
        server='virprdyouslm01',
        username='YoudocPRDPH-DFT-svc',
        password='DgPJnwR3E$v4x7$a',
        tenant='PH',
        port='8984',  # Default port for SOLR Server, change if different
        start_date=args.start_date,
        end_date=args.end_date,
        filePath='resultat_solr.txt'
    )

    # On supprime les doublons pour ne réindexer que les documents non-presents dans SOLR
    remove_duplicates.remove_duplicates('resultat_sgbd.txt', 'resultat_solr.txt', 'resultat_delta.txt')
    remove_duplicates.extract_non_duplicates('resultat_sgbd.txt', 'resultat_solr.txt', 'resultat_delta.txt')
   
    # On met à jour les documents ou dossiers en BDD pour réindexation
    update_sql.update_sql_from_file(
        file_path='resultat_delta.txt',
        server='o75PRD',
        db_type='DB2',
        username='YDOCADM',
        password='T9S7UHT545',
        database='YDOCDTAPH',
        port='446',  # Default port for DB2 Server, change if different
        table_name='YDOCDTAPH.ARG0CPP',
        update_column='DDr68A',
        criterion_column='DD1rA'
    )

if __name__ == "__main__":
    main()