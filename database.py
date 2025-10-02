import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    """Conecta ao banco correto (PostgreSQL no Railway, SQLite local)"""
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # PostgreSQL (Railway)
        conn = psycopg2.connect(database_url)
        return conn, 'postgresql'
    else:
        # SQLite (local)
        conn = sqlite3.connect('ameg.db')
        conn.row_factory = sqlite3.Row
        return conn, 'sqlite'

def init_db_tables():
    """Cria as tabelas necessárias"""
    conn, db_type = get_db_connection()
    
    if db_type == 'postgresql':
        cursor = conn.cursor()
        
        # Tabela usuarios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                usuario VARCHAR(50) UNIQUE NOT NULL,
                senha VARCHAR(255) NOT NULL
            )
        ''')
        
        # Tabela cadastros
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cadastros (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                endereco TEXT,
                bairro VARCHAR(100),
                telefone VARCHAR(20),
                genero VARCHAR(20),
                idade INTEGER,
                cpf VARCHAR(14),
                rg VARCHAR(20),
                data_nascimento DATE,
                estado_civil VARCHAR(30),
                profissao VARCHAR(100),
                renda_familiar DECIMAL(10,2),
                pessoas_familia INTEGER,
                doencas_cronicas TEXT,
                medicamentos TEXT,
                deficiencias TEXT,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela arquivos_saude
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS arquivos_saude (
                id SERIAL PRIMARY KEY,
                cadastro_id INTEGER REFERENCES cadastros(id),
                nome_arquivo VARCHAR(255) NOT NULL,
                caminho_arquivo TEXT NOT NULL,
                tipo_arquivo VARCHAR(50),
                data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
    else:
        # SQLite (código original)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cadastros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                endereco TEXT,
                bairro TEXT,
                telefone TEXT,
                genero TEXT,
                idade INTEGER,
                cpf TEXT,
                rg TEXT,
                data_nascimento TEXT,
                estado_civil TEXT,
                profissao TEXT,
                renda_familiar REAL,
                pessoas_familia INTEGER,
                doencas_cronicas TEXT,
                medicamentos TEXT,
                deficiencias TEXT,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS arquivos_saude (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cadastro_id INTEGER,
                nome_arquivo TEXT NOT NULL,
                caminho_arquivo TEXT NOT NULL,
                tipo_arquivo TEXT,
                data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cadastro_id) REFERENCES cadastros (id)
            )
        ''')
    
    conn.commit()
    conn.close()

def create_admin_user():
    """Cria usuário admin"""
    from werkzeug.security import generate_password_hash
    import secrets
    import string
    
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar se já existe admin
    if db_type == 'postgresql':
        cursor.execute('SELECT COUNT(*) FROM usuarios WHERE usuario = %s', ('admin',))
    else:
        cursor.execute('SELECT COUNT(*) FROM usuarios WHERE usuario = ?', ('admin',))
    
    if cursor.fetchone()[0] > 0:
        conn.close()
        return
    
    # Gerar senha
    admin_password = os.environ.get('ADMIN_PASSWORD')
    if not admin_password:
        chars = string.ascii_letters + string.digits + "!@#$%&*"
        admin_password = ''.join(secrets.choice(chars) for _ in range(16))
        print(f"SENHA ADMIN GERADA: {admin_password}")
    
    senha_hash = generate_password_hash(admin_password)
    
    # Inserir admin
    if db_type == 'postgresql':
        cursor.execute('INSERT INTO usuarios (usuario, senha) VALUES (%s, %s)', ('admin', senha_hash))
    else:
        cursor.execute('INSERT INTO usuarios (usuario, senha) VALUES (?, ?)', ('admin', senha_hash))
    
    conn.commit()
    conn.close()
