import os
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash
import logging

logger = logging.getLogger(__name__)

def get_db_connection():
    """Conecta ao PostgreSQL do Railway"""
    database_url = os.environ.get('DATABASE_URL')
    logger.debug(f"DATABASE_URL presente: {bool(database_url)}")
    
    if not database_url:
        logger.error("DATABASE_URL não encontrada nas variáveis de ambiente")
        raise Exception("DATABASE_URL não encontrada")
    
    logger.debug("Tentando conectar ao PostgreSQL...")
    try:
        conn = psycopg2.connect(database_url)
        logger.debug("✅ Conexão PostgreSQL estabelecida")
        return conn
    except Exception as e:
        logger.error(f"❌ Erro ao conectar PostgreSQL: {e}")
        raise

def init_db_tables():
    """Cria as tabelas necessárias no PostgreSQL"""
    logger.info("🔧 Iniciando criação de tabelas...")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        logger.debug("Cursor criado para init_db_tables")
        
        # Tabela usuarios
        logger.debug("Criando tabela usuarios...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                usuario VARCHAR(50) UNIQUE NOT NULL,
                senha VARCHAR(255) NOT NULL
            )
        ''')
        logger.debug("✅ Tabela usuarios criada/verificada")
        
        # Dropar e recriar tabela cadastros para garantir estrutura atualizada
        logger.debug("Recriando tabela cadastros...")
        cursor.execute('DROP TABLE IF EXISTS cadastros CASCADE')
        logger.debug("Tabela cadastros dropada (se existia)")
        
        # Tabela cadastros - TODOS os campos do formulário
        logger.debug("Criando nova tabela cadastros...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cadastros (
                id SERIAL PRIMARY KEY,
                nome_completo VARCHAR(255) NOT NULL,
                endereco TEXT,
                numero VARCHAR(10),
                bairro VARCHAR(100),
                cep VARCHAR(10),
                telefone VARCHAR(20),
                ponto_referencia TEXT,
                genero VARCHAR(50),
                idade INTEGER,
                data_nascimento DATE,
                titulo_eleitor VARCHAR(20),
                cidade_titulo VARCHAR(100),
                cpf VARCHAR(14),
                rg VARCHAR(20),
                nis VARCHAR(20),
                estado_civil VARCHAR(30),
                escolaridade VARCHAR(100),
                profissao VARCHAR(100),
                nome_companheiro VARCHAR(255),
                cpf_companheiro VARCHAR(14),
                rg_companheiro VARCHAR(20),
                idade_companheiro INTEGER,
                escolaridade_companheiro VARCHAR(100),
                profissao_companheiro VARCHAR(100),
                data_nascimento_companheiro DATE,
                titulo_companheiro VARCHAR(20),
                cidade_titulo_companheiro VARCHAR(100),
                nis_companheiro VARCHAR(20),
                tipo_trabalho VARCHAR(100),
                pessoas_trabalham INTEGER,
                aposentados_pensionistas INTEGER,
                num_pessoas_familia INTEGER,
                num_familias INTEGER,
                adultos INTEGER,
                criancas INTEGER,
                adolescentes INTEGER,
                idosos INTEGER,
                gestantes INTEGER,
                nutrizes INTEGER,
                renda_familiar DECIMAL(10,2),
                renda_per_capita DECIMAL(10,2),
                bolsa_familia DECIMAL(10,2),
                casa_tipo VARCHAR(50),
                casa_material VARCHAR(50),
                energia VARCHAR(10),
                lixo VARCHAR(10),
                agua VARCHAR(10),
                esgoto VARCHAR(10),
                observacoes TEXT,
                tem_doenca_cronica VARCHAR(10),
                doencas_cronicas TEXT,
                usa_medicamento_continuo VARCHAR(10),
                medicamentos_continuos TEXT,
                tem_doenca_mental VARCHAR(10),
                doencas_mentais TEXT,
                tem_deficiencia VARCHAR(10),
                tipo_deficiencia TEXT,
                precisa_cuidados_especiais VARCHAR(10),
                cuidados_especiais TEXT,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        logger.debug("✅ Tabela cadastros criada")
        
        # Tabela arquivos_saude
        logger.debug("Criando tabela arquivos_saude...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS arquivos_saude (
                id SERIAL PRIMARY KEY,
                cadastro_id INTEGER REFERENCES cadastros(id) ON DELETE CASCADE,
                nome_arquivo VARCHAR(255) NOT NULL,
                tipo_arquivo VARCHAR(50),
                descricao TEXT,
                arquivo_dados BYTEA,
                data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        logger.debug("✅ Tabela arquivos_saude criada")
        
        conn.commit()
        logger.debug("✅ Commit realizado")
        cursor.close()
        conn.close()
        logger.info("✅ Todas as tabelas criadas com sucesso")
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar tabelas: {e}")
        logger.error(f"Tipo do erro: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

def create_admin_user():
    """Cria usuário admin padrão"""
    logger.info("👤 Criando usuário admin...")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        logger.debug("Cursor criado para create_admin_user")
        
        # Verificar se admin já existe
        logger.debug("Verificando se admin já existe...")
        cursor.execute('SELECT id FROM usuarios WHERE usuario = %s', ('admin',))
        existing_admin = cursor.fetchone()
        
        if existing_admin:
            logger.info("ℹ️ Usuário admin já existe")
            cursor.close()
            conn.close()
            return
        
        # Criar admin
        admin_password = os.environ.get('ADMIN_PASSWORD', 'Admin@2024!Secure')
        logger.debug(f"Senha admin configurada: {bool(admin_password)}")
        
        senha_hash = generate_password_hash(admin_password)
        logger.debug("Hash da senha gerado")
        
        cursor.execute('INSERT INTO usuarios (usuario, senha) VALUES (%s, %s)', ('admin', senha_hash))
        logger.debug("Query INSERT executada")
        
        conn.commit()
        logger.debug("Commit realizado")
        cursor.close()
        conn.close()
        logger.info("✅ Usuário admin criado com sucesso")
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar admin: {e}")
        logger.error(f"Tipo do erro: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
