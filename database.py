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
        
        # Tabela cadastros - TODOS os campos do formulário
        logger.debug("Criando tabela cadastros...")
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
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- ATIVIDADE DE TRABALHO
                com_que_trabalha TEXT,
                onde_trabalha TEXT,
                horario_trabalho TEXT,
                tempo_atividade TEXT,
                atua_ponto_fixo VARCHAR(10),
                qual_ponto_fixo TEXT,
                dias_semana_trabalha INTEGER,
                trabalho_continuo_temporada VARCHAR(20),
                
                -- CONDIÇÕES DE TRABALHO
                sofreu_acidente_trabalho VARCHAR(10),
                qual_acidente TEXT,
                trabalho_incomoda_calor VARCHAR(10),
                trabalho_incomoda_barulho VARCHAR(10),
                trabalho_incomoda_seguranca VARCHAR(10),
                trabalho_incomoda_banheiros VARCHAR(10),
                trabalho_incomoda_outro VARCHAR(10),
                trabalho_incomoda_outro_desc TEXT,
                acesso_banheiro_agua VARCHAR(10),
                trabalha_sozinho_ajudantes TEXT,
                possui_autorizacao_municipal VARCHAR(10),
                problemas_fiscalizacao_policia VARCHAR(10),
                
                -- ESTRUTURA DE TRABALHO
                estrutura_barraca VARCHAR(10),
                estrutura_carrinho VARCHAR(10),
                estrutura_mesa VARCHAR(10),
                estrutura_outro VARCHAR(10),
                estrutura_outro_desc TEXT,
                necessita_energia_eletrica VARCHAR(10),
                utiliza_gas_cozinha VARCHAR(10),
                usa_veiculo_proprio VARCHAR(10),
                qual_veiculo TEXT,
                
                -- RENDA E FAMÍLIA
                fonte_renda_trabalho_ambulante VARCHAR(10),
                fonte_renda_aposentadoria VARCHAR(10),
                fonte_renda_outro_trabalho VARCHAR(10),
                fonte_renda_beneficio_social VARCHAR(10),
                fonte_renda_outro VARCHAR(10),
                fonte_renda_outro_desc TEXT,
                pessoas_dependem_renda INTEGER
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
