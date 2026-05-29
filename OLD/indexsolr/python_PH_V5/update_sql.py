import pyodbc

def update_sql_from_file(file_path, server, db_type, database, port, username, password, table_name, update_column, criterion_column):
    # Connexion à la base de données en fonction du type (SQL ou DB2)
    if db_type == 'DB2':
        conn_str = f'DRIVER={{iSeries access ODBC Driver}};SYSTEM={server};PORT={port};DATABASE={database};PROTOCOL=TCPIP;UID={username};PWD={password}'
    else:
        conn_str = f'DRIVER={{SQL Server}};SERVER={server};PORT={port};DATABASE={database};UID={username};PWD={password};Trusted_Connection=No;'

    try:
        # Establish connection
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        # Read the file
        with open(file_path, 'r') as file:
            for line in file:
                criterion_value = line.strip()
                
                # SQL update statement
                sql = f"""
                UPDATE {table_name}
                SET {update_column} = 'N'
                WHERE {criterion_column} = ?
                """

                if (db_type == 'DB2'):
                    sql += " WITH NC"

                # Execute the update for each line in the file
                cursor.execute(sql, criterion_value)
                #print(f"Updated rows where {criterion_column} = {criterion_value}")

        # Commit the transaction
        conn.commit()
        print("All updates completed successfully.")

    except pyodbc.Error as e:
        print(f"Database error: {str(e)}")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()
