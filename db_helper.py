import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db():
    """Conecta ao banco correto e retorna conexão padronizada"""
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # PostgreSQL
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        return conn, 'postgresql'
    else:
        # SQLite
        conn = sqlite3.connect('ameg.db')
        conn.row_factory = sqlite3.Row
        return conn, 'sqlite'

def execute_query(query, params=None, fetch=False):
    """Executa query adaptada para ambos os bancos"""
    conn, db_type = get_db()
    cursor = conn.cursor()
    
    try:
        # Adaptar query para PostgreSQL
        if db_type == 'postgresql' and params:
            # Converter ? para %s
            adapted_query = query.replace('?', '%s')
            cursor.execute(adapted_query, params)
        else:
            cursor.execute(query, params or ())
        
        if fetch:
            result = cursor.fetchall()
            conn.close()
            return result
        else:
            conn.commit()
            result = cursor.lastrowid if db_type == 'sqlite' else cursor.rowcount
            conn.close()
            return result
    except Exception as e:
        conn.close()
        # Se falhar no PostgreSQL, tentar inicializar tabelas
        if db_type == 'postgresql':
            from database import init_db_tables, create_admin_user
            try:
                init_db_tables()
                create_admin_user()
                # Tentar novamente
                return execute_query(query, params, fetch)
            except:
                pass
        raise e
