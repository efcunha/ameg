import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

logger = logging.getLogger(__name__)

def get_db():
    """Conecta ao banco correto e retorna conexão padronizada"""
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # PostgreSQL
        logger.debug("Conectando ao PostgreSQL via DATABASE_URL")
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        logger.debug("✅ Conexão PostgreSQL estabelecida")
        return conn, 'postgresql'
    else:
        # SQLite
        logger.debug("Conectando ao SQLite local")
        conn = sqlite3.connect('ameg.db')
        conn.row_factory = sqlite3.Row
        logger.debug("✅ Conexão SQLite estabelecida")
        return conn, 'sqlite'

def execute_query(query, params=None, fetch=False):
    """Executa query adaptada para ambos os bancos"""
    logger.debug(f"Executando query: {query[:100]}...")
    conn, db_type = get_db()
    cursor = conn.cursor()
    
    try:
        # Adaptar query para PostgreSQL
        if db_type == 'postgresql' and params:
            # Converter ? para %s
            adapted_query = query.replace('?', '%s')
            logger.debug(f"Query adaptada para PostgreSQL")
            cursor.execute(adapted_query, params)
        else:
            cursor.execute(query, params or ())
        
        if fetch:
            result = cursor.fetchall()
            logger.debug(f"Query retornou {len(result) if result else 0} registros")
            conn.close()
            return result
        else:
            conn.commit()
            logger.debug("✅ Query executada e commitada com sucesso")
            if db_type == 'sqlite':
                result = cursor.lastrowid
            else:
                # PostgreSQL - retornar número de linhas afetadas
                result = cursor.rowcount
            conn.close()
            return result
    except Exception as e:
        logger.error(f"❌ Erro ao executar query: {e}")
        logger.error(f"Query: {query[:200]}...")
        logger.error(f"Params: {params}")
        conn.close()
        # Se falhar no PostgreSQL, tentar inicializar tabelas
        if db_type == 'postgresql':
            logger.warning("⚠️ Tentando inicializar tabelas automaticamente...")
            from database import init_db_tables, create_admin_user
            try:
                init_db_tables()
                create_admin_user()
                logger.info("✅ Tabelas inicializadas, tentando query novamente...")
                # Tentar novamente
                return execute_query(query, params, fetch)
            except Exception as init_error:
                logger.error(f"❌ Falha na inicialização automática: {init_error}")
        raise e
