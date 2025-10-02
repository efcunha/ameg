import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash

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
                nome_completo VARCHAR(255) NOT NULL,
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
                num_pessoas_familia INTEGER,
                tem_doenca_cronica VARCHAR(10),
                doencas_cronicas TEXT,
                usa_medicamento_continuo VARCHAR(10),
                medicamentos_continuos TEXT,
                tem_doenca_mental VARCHAR(10),
                doencas_mentais TEXT,
                tem_deficiencia VARCHAR(10),
                deficiencias TEXT,
                precisa_cuidados_especiais VARCHAR(10),
                cuidados_especiais TEXT,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela arquivos_saude
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS arquivos_saude (
                id SERIAL PRIMARY KEY,
                cadastro_id INTEGER,
                nome_arquivo VARCHAR(255) NOT NULL,
                tipo_arquivo VARCHAR(50),
                caminho_arquivo TEXT NOT NULL,
                data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cadastro_id) REFERENCES cadastros (id)
            )
        ''')
        
        conn.commit()
        cursor.close()
        conn.close()
        
    else:
        # SQLite
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
                nome_completo TEXT NOT NULL,
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
                num_pessoas_familia INTEGER,
                tem_doenca_cronica TEXT,
                doencas_cronicas TEXT,
                usa_medicamento_continuo TEXT,
                medicamentos_continuos TEXT,
                tem_doenca_mental TEXT,
                doencas_mentais TEXT,
                tem_deficiencia TEXT,
                deficiencias TEXT,
                precisa_cuidados_especiais TEXT,
                cuidados_especiais TEXT,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS arquivos_saude (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cadastro_id INTEGER,
                nome_arquivo TEXT NOT NULL,
                tipo_arquivo TEXT,
                caminho_arquivo TEXT NOT NULL,
                data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cadastro_id) REFERENCES cadastros (id)
            )
        ''')
        
        conn.commit()
        conn.close()

def create_admin_user():
    """Cria usuário admin se não existir"""
    conn, db_type = get_db_connection()
    
    if db_type == 'postgresql':
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM usuarios WHERE usuario = %s', ('admin',))
        if cursor.fetchone()[0] == 0:
            admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
            senha_hash = generate_password_hash(admin_password)
            cursor.execute('INSERT INTO usuarios (usuario, senha) VALUES (%s, %s)', ('admin', senha_hash))
            conn.commit()
        cursor.close()
        conn.close()
    else:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM usuarios WHERE usuario = ?', ('admin',))
        if cursor.fetchone()[0] == 0:
            senha_hash = generate_password_hash('admin123')
            cursor.execute('INSERT INTO usuarios (usuario, senha) VALUES (?, ?)', ('admin', senha_hash))
            conn.commit()
        conn.close()
