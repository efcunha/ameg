import os
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash
import logging

# Importar security manager
try:
    from security import security_manager
except ImportError:
    security_manager = None
    logging.warning("Security manager não disponível - usando fallback")

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
                senha VARCHAR(255) NOT NULL,
                tipo VARCHAR(20) DEFAULT 'usuario'
            )
        ''')
        logger.debug("✅ Tabela usuarios criada/verificada")
        
        # Adicionar coluna tipo se não existir (para compatibilidade)
        try:
            cursor.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS tipo VARCHAR(20) DEFAULT 'usuario'")
            logger.debug("✅ Coluna tipo adicionada/verificada")
        except Exception as e:
            logger.debug(f"Coluna tipo já existe ou erro: {e}")
        
        # Atualizar admin existente para tipo 'admin'
        try:
            cursor.execute("UPDATE usuarios SET tipo = 'admin' WHERE usuario = 'admin'")
            logger.debug("✅ Tipo do admin atualizado")
        except Exception as e:
            logger.debug(f"Erro ao atualizar tipo do admin: {e}")
        
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
                medicamento_alto_custo VARCHAR(10),
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
        
        # Verificar e adicionar campo localizacao_trabalho se não existir
        logger.debug("Verificando se campo localizacao_trabalho existe...")
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'cadastros' AND column_name = 'localizacao_trabalho'
        """)
        localizacao_existe = cursor.fetchone()
        
        if not localizacao_existe:
            logger.info("🔧 Adicionando campo localizacao_trabalho à tabela...")
            cursor.execute("ALTER TABLE cadastros ADD COLUMN IF NOT EXISTS localizacao_trabalho VARCHAR(50)")
            logger.info("✅ Campo localizacao_trabalho adicionado!")
        else:
            logger.debug("✅ Campo localizacao_trabalho já existe")
        
        # Verificar e adicionar campos cidade e estado se não existirem
        logger.debug("Verificando se campos cidade e estado existem...")
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'cadastros' AND column_name = 'cidade'
        """)
        cidade_existe = cursor.fetchone()
        
        if not cidade_existe:
            logger.info("🔧 Adicionando campos cidade e estado à tabela...")
            cursor.execute("ALTER TABLE cadastros ADD COLUMN IF NOT EXISTS cidade VARCHAR(100)")
            cursor.execute("ALTER TABLE cadastros ADD COLUMN IF NOT EXISTS estado VARCHAR(2)")
            logger.info("✅ Campos cidade e estado adicionados!")
        else:
            logger.debug("✅ Campos cidade e estado já existem")
        
        # Verificar e adicionar novos campos se não existirem
        logger.debug("Verificando se novos campos de trabalho existem...")
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'cadastros' AND column_name = 'com_que_trabalha'
        """)
        campo_existe = cursor.fetchone()
        
        if not campo_existe:
            logger.info("🔧 Adicionando novos campos de trabalho à tabela existente...")
            
            # Adicionar campos de atividade de trabalho
            cursor.execute("ALTER TABLE cadastros ADD COLUMN IF NOT EXISTS com_que_trabalha TEXT")
            cursor.execute("ALTER TABLE cadastros ADD COLUMN IF NOT EXISTS onde_trabalha TEXT")
            cursor.execute("ALTER TABLE cadastros ADD COLUMN IF NOT EXISTS horario_trabalho TEXT")
            cursor.execute("ALTER TABLE cadastros ADD COLUMN IF NOT EXISTS tempo_atividade TEXT")
            cursor.execute("ALTER TABLE cadastros ADD COLUMN IF NOT EXISTS atua_ponto_fixo VARCHAR(10)")
            cursor.execute("ALTER TABLE cadastros ADD COLUMN IF NOT EXISTS qual_ponto_fixo TEXT")
            cursor.execute("ALTER TABLE cadastros ADD COLUMN IF NOT EXISTS dias_semana_trabalha INTEGER")
            cursor.execute("ALTER TABLE cadastros ADD COLUMN IF NOT EXISTS trabalho_continuo_temporada VARCHAR(20)")
            
            # Adicionar campos de condições de trabalho
            cursor.execute("ALTER TABLE cadastros ADD COLUMN IF NOT EXISTS sofreu_acidente_trabalho VARCHAR(10)")
            cursor.execute("ALTER TABLE cadastros ADD COLUMN IF NOT EXISTS qual_acidente TEXT")
            cursor.execute("ALTER TABLE cadastros ADD COLUMN IF NOT EXISTS trabalho_incomoda_calor VARCHAR(10)")
            cursor.execute("ALTER TABLE cadastros ADD COLUMN IF NOT EXISTS trabalho_incomoda_barulho VARCHAR(10)")
            cursor.execute("ALTER TABLE cadastros ADD COLUMN IF NOT EXISTS trabalho_incomoda_seguranca VARCHAR(10)")
            cursor.execute("ALTER TABLE cadastros ADD COLUMN IF NOT EXISTS trabalho_incomoda_banheiros VARCHAR(10)")
            cursor.execute("ALTER TABLE cadastros ADD COLUMN IF NOT EXISTS trabalho_incomoda_outro VARCHAR(10)")
            cursor.execute("ALTER TABLE cadastros ADD COLUMN IF NOT EXISTS trabalho_incomoda_outro_desc TEXT")
            cursor.execute("ALTER TABLE cadastros ADD COLUMN IF NOT EXISTS acesso_banheiro_agua VARCHAR(10)")
            cursor.execute("ALTER TABLE cadastros ADD COLUMN IF NOT EXISTS trabalha_sozinho_ajudantes TEXT")
            cursor.execute("ALTER TABLE cadastros ADD COLUMN IF NOT EXISTS possui_autorizacao_municipal VARCHAR(10)")
            cursor.execute("ALTER TABLE cadastros ADD COLUMN IF NOT EXISTS problemas_fiscalizacao_policia VARCHAR(10)")
            
            # Adicionar campos de estrutura de trabalho
            cursor.execute("ALTER TABLE cadastros ADD COLUMN IF NOT EXISTS estrutura_barraca VARCHAR(10)")
            cursor.execute("ALTER TABLE cadastros ADD COLUMN IF NOT EXISTS estrutura_carrinho VARCHAR(10)")
            cursor.execute("ALTER TABLE cadastros ADD COLUMN IF NOT EXISTS estrutura_mesa VARCHAR(10)")
            cursor.execute("ALTER TABLE cadastros ADD COLUMN IF NOT EXISTS estrutura_outro VARCHAR(10)")
            cursor.execute("ALTER TABLE cadastros ADD COLUMN IF NOT EXISTS estrutura_outro_desc TEXT")
            cursor.execute("ALTER TABLE cadastros ADD COLUMN IF NOT EXISTS necessita_energia_eletrica VARCHAR(10)")
            cursor.execute("ALTER TABLE cadastros ADD COLUMN IF NOT EXISTS utiliza_gas_cozinha VARCHAR(10)")
            cursor.execute("ALTER TABLE cadastros ADD COLUMN IF NOT EXISTS usa_veiculo_proprio VARCHAR(10)")
            cursor.execute("ALTER TABLE cadastros ADD COLUMN IF NOT EXISTS qual_veiculo TEXT")
            
            # Adicionar campos de renda e família
            cursor.execute("ALTER TABLE cadastros ADD COLUMN IF NOT EXISTS fonte_renda_trabalho_ambulante VARCHAR(10)")
            cursor.execute("ALTER TABLE cadastros ADD COLUMN IF NOT EXISTS fonte_renda_aposentadoria VARCHAR(10)")
            cursor.execute("ALTER TABLE cadastros ADD COLUMN IF NOT EXISTS fonte_renda_outro_trabalho VARCHAR(10)")
            cursor.execute("ALTER TABLE cadastros ADD COLUMN IF NOT EXISTS fonte_renda_beneficio_social VARCHAR(10)")
            cursor.execute("ALTER TABLE cadastros ADD COLUMN IF NOT EXISTS fonte_renda_outro VARCHAR(10)")
            cursor.execute("ALTER TABLE cadastros ADD COLUMN IF NOT EXISTS fonte_renda_outro_desc TEXT")
            cursor.execute("ALTER TABLE cadastros ADD COLUMN IF NOT EXISTS pessoas_dependem_renda INTEGER")
            
            logger.info("✅ Novos campos adicionados com sucesso!")
        else:
            logger.debug("✅ Campos de trabalho já existem na tabela")
        
        # Verificar e adicionar campo foto_base64 se não existir
        logger.debug("Verificando se campo foto_base64 existe...")
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'cadastros' AND column_name = 'foto_base64'
        """)
        foto_existe = cursor.fetchone()
        
        if not foto_existe:
            logger.info("🔧 Adicionando campo foto_base64 à tabela...")
            cursor.execute("ALTER TABLE cadastros ADD COLUMN IF NOT EXISTS foto_base64 TEXT")
            logger.info("✅ Campo foto_base64 adicionado!")
        else:
            logger.debug("✅ Campo foto_base64 já existe na tabela")
        
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
        
        # Verificar e adicionar coluna arquivo_dados se não existir
        logger.debug("Verificando se coluna arquivo_dados existe...")
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'arquivos_saude' AND column_name = 'arquivo_dados'
        """)
        coluna_existe = cursor.fetchone()
        
        if not coluna_existe:
            logger.info("🔧 Adicionando coluna arquivo_dados à tabela arquivos_saude...")
            cursor.execute("ALTER TABLE arquivos_saude ADD COLUMN arquivo_dados BYTEA")
            logger.info("✅ Coluna arquivo_dados adicionada!")
        else:
            logger.debug("✅ Coluna arquivo_dados já existe")
        
        # Verificar e tornar caminho_arquivo opcional se existir
        logger.debug("Verificando se coluna caminho_arquivo existe...")
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'arquivos_saude' AND column_name = 'caminho_arquivo'
        """)
        caminho_existe = cursor.fetchone()
        
        if caminho_existe:
            logger.info("🔧 Tornando coluna caminho_arquivo opcional...")
            cursor.execute("ALTER TABLE arquivos_saude ALTER COLUMN caminho_arquivo DROP NOT NULL")
            logger.info("✅ Coluna caminho_arquivo agora é opcional!")
        else:
            logger.debug("✅ Coluna caminho_arquivo não existe")
            
        logger.debug("✅ Tabela arquivos_saude criada")
        
        # Criar tabela dados_saude_pessoa
        logger.debug("Criando tabela dados_saude_pessoa...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dados_saude_pessoa (
                id SERIAL PRIMARY KEY,
                cadastro_id INTEGER REFERENCES cadastros(id) ON DELETE CASCADE,
                nome_pessoa VARCHAR(255) NOT NULL,
                tem_doenca_cronica VARCHAR(10),
                doencas_cronicas TEXT,
                usa_medicamento_continuo VARCHAR(10),
                medicamentos TEXT,
                tem_doenca_mental VARCHAR(10),
                doencas_mentais TEXT,
                tem_deficiencia VARCHAR(10),
                deficiencias TEXT,
                precisa_cuidados_especiais VARCHAR(10),
                cuidados_especiais TEXT,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        logger.debug("✅ Tabela dados_saude_pessoa criada")
        
        # Tabela auditoria
        logger.debug("Criando tabela auditoria...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS auditoria (
                id SERIAL PRIMARY KEY,
                usuario VARCHAR(100) NOT NULL,
                acao VARCHAR(50) NOT NULL,
                tabela VARCHAR(50) NOT NULL,
                registro_id INTEGER,
                dados_anteriores TEXT,
                dados_novos TEXT,
                ip_address VARCHAR(45),
                user_agent TEXT,
                data_acao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        logger.debug("✅ Tabela auditoria criada")
        
        # Criar índices para otimização de performance
        logger.debug("Criando índices de otimização...")
        
        # Índices para tabela cadastros
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_cadastros_cpf ON cadastros(cpf)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_cadastros_nome ON cadastros(nome_completo)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_cadastros_data ON cadastros(data_cadastro)')
        
        # Índices para tabela auditoria
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_auditoria_usuario ON auditoria(usuario)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_auditoria_data ON auditoria(data_acao)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_auditoria_tabela ON auditoria(tabela)')
        
        # Índices para tabela arquivos_saude
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_arquivos_cadastro ON arquivos_saude(cadastro_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_arquivos_data ON arquivos_saude(data_upload)')
        
        # Índices para tabela dados_saude_pessoa
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_saude_pessoa_cadastro ON dados_saude_pessoa(cadastro_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_saude_pessoa_nome ON dados_saude_pessoa(nome_pessoa)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_saude_pessoa_data ON dados_saude_pessoa(data_cadastro)')
        
        logger.debug("✅ Índices de otimização criados")
        
        # Tabela movimentacoes_caixa
        logger.debug("Criando tabela movimentacoes_caixa...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS movimentacoes_caixa (
                id SERIAL PRIMARY KEY,
                tipo VARCHAR(10) NOT NULL CHECK (tipo IN ('entrada', 'saida')),
                valor DECIMAL(10,2) NOT NULL,
                descricao TEXT NOT NULL,
                cadastro_id INTEGER REFERENCES cadastros(id),
                nome_pessoa VARCHAR(255),
                numero_recibo VARCHAR(50),
                observacoes TEXT,
                data_movimentacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                usuario VARCHAR(100) NOT NULL
            )
        ''')
        logger.debug("✅ Tabela movimentacoes_caixa criada")
        
        # Tabela comprovantes_caixa
        logger.debug("Criando tabela comprovantes_caixa...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comprovantes_caixa (
                id SERIAL PRIMARY KEY,
                movimentacao_id INTEGER REFERENCES movimentacoes_caixa(id) ON DELETE CASCADE,
                nome_arquivo VARCHAR(255) NOT NULL,
                tipo_arquivo VARCHAR(50),
                arquivo_dados BYTEA,
                data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        logger.debug("✅ Tabela comprovantes_caixa criada")
        
        # Tabela permissoes_usuario
        logger.debug("Criando tabela permissoes_usuario...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS permissoes_usuario (
                id SERIAL PRIMARY KEY,
                usuario_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
                permissao VARCHAR(50) NOT NULL,
                UNIQUE(usuario_id, permissao)
            )
        ''')
        logger.debug("✅ Tabela permissoes_usuario criada")
        
        # Tabela histórico de notificações
        logger.debug("Criando tabela historico_notificacoes...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historico_notificacoes (
                id SERIAL PRIMARY KEY,
                tipo VARCHAR(20) NOT NULL,
                prioridade VARCHAR(10) NOT NULL,
                mensagem TEXT NOT NULL,
                icone VARCHAR(10),
                cadastro_id INTEGER REFERENCES cadastros(id) ON DELETE CASCADE,
                visualizada BOOLEAN DEFAULT FALSE,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_visualizacao TIMESTAMP
            )
        ''')
        logger.debug("✅ Tabela historico_notificacoes criada")
        
        # Índices para tabelas de caixa
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_caixa_tipo ON movimentacoes_caixa(tipo)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_caixa_data ON movimentacoes_caixa(data_movimentacao)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_caixa_cadastro ON movimentacoes_caixa(cadastro_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_caixa_usuario ON movimentacoes_caixa(usuario)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_comprovantes_movimentacao ON comprovantes_caixa(movimentacao_id)')
        
        # Índices para tabela permissoes_usuario
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_permissoes_usuario ON permissoes_usuario(usuario_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_permissoes_permissao ON permissoes_usuario(permissao)')
        
        # Índices para tabela historico_notificacoes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_notificacoes_tipo ON historico_notificacoes(tipo)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_notificacoes_visualizada ON historico_notificacoes(visualizada)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_notificacoes_data ON historico_notificacoes(data_criacao)')
        
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
    """Cria usuário admin padrão com proteção adicional"""
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
        
        # Criar admin com proteção adicional
        admin_password = os.environ.get('ADMIN_PASSWORD', 'Admin@2024!Secure')
        logger.debug(f"Senha admin configurada: {bool(admin_password)}")
        
        # Usar security manager se disponível
        if security_manager:
            senha_hash = security_manager.hash_admin_password(admin_password)
            logger.debug("Hash da senha gerado com security manager")
        else:
            senha_hash = generate_password_hash(admin_password)
            logger.debug("Hash da senha gerado com fallback")
        
        cursor.execute('INSERT INTO usuarios (usuario, senha, tipo) VALUES (%s, %s, %s)', 
                      ('admin', senha_hash, 'admin'))
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
def registrar_auditoria(usuario, acao, tabela, registro_id=None, dados_anteriores=None, dados_novos=None, ip_address=None, user_agent=None):
    """Registra uma ação de auditoria no banco de dados"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO auditoria (usuario, acao, tabela, registro_id, dados_anteriores, dados_novos, ip_address, user_agent)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (usuario, acao, tabela, registro_id, dados_anteriores, dados_novos, ip_address, user_agent))
        
        conn.commit()
        cursor.close()
        conn.close()
        logger.debug(f"✅ Auditoria registrada: {usuario} - {acao} - {tabela}")
        
    except Exception as e:
        logger.error(f"❌ Erro ao registrar auditoria: {e}")

# Funções para sistema de caixa
def inserir_movimentacao_caixa(tipo, valor, descricao, cadastro_id, nome_pessoa, numero_recibo, observacoes, usuario):
    """Insere uma nova movimentação no caixa"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO movimentacoes_caixa (tipo, valor, descricao, cadastro_id, nome_pessoa, numero_recibo, observacoes, usuario)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (tipo, valor, descricao, cadastro_id, nome_pessoa, numero_recibo, observacoes, usuario))
        
        movimentacao_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        # Registrar auditoria
        registrar_auditoria(usuario, 'INSERT', 'movimentacoes_caixa', movimentacao_id, 
                          None, f"Tipo: {tipo}, Valor: {valor}, Descrição: {descricao}")
        
        return movimentacao_id
        
    except Exception as e:
        logger.error(f"❌ Erro ao inserir movimentação: {e}")
        raise

def inserir_comprovante_caixa(movimentacao_id, nome_arquivo, tipo_arquivo, arquivo_dados):
    """Insere um comprovante para uma movimentação"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO comprovantes_caixa (movimentacao_id, nome_arquivo, tipo_arquivo, arquivo_dados)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        ''', (movimentacao_id, nome_arquivo, tipo_arquivo, arquivo_dados))
        
        comprovante_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        return comprovante_id
        
    except Exception as e:
        logger.error(f"❌ Erro ao inserir comprovante: {e}")
        raise

def listar_movimentacoes_caixa(limit=50, offset=0, tipo=None):
    """Lista movimentações do caixa com paginação"""
    try:
        logger.info("=== INICIANDO listar_movimentacoes_caixa ===")
        logger.info(f"Parâmetros: limit={limit}, offset={offset}, tipo={tipo}")
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        logger.info("Conexão estabelecida para listar_movimentacoes_caixa")
        
        where_clause = ""
        params = []
        
        if tipo:
            where_clause = "WHERE m.tipo = %s"
            params.append(tipo)
            logger.info(f"Filtro por tipo aplicado: {tipo}")
        
        query = f'''
            SELECT m.*, c.nome_completo as nome_cadastro,
                   COUNT(comp.id) as total_comprovantes
            FROM movimentacoes_caixa m
            LEFT JOIN cadastros c ON m.cadastro_id = c.id
            LEFT JOIN comprovantes_caixa comp ON m.id = comp.movimentacao_id
            {where_clause}
            GROUP BY m.id, c.nome_completo
            ORDER BY m.data_movimentacao DESC
            LIMIT %s OFFSET %s
        '''
        
        params.extend([limit, offset])
        logger.info(f"Executando query: {query}")
        logger.info(f"Parâmetros: {params}")
        
        cursor.execute(query, params)
        movimentacoes = cursor.fetchall()
        logger.info(f"Movimentações encontradas: {len(movimentacoes)}")
        
        cursor.close()
        conn.close()
        logger.info("Conexão fechada para listar_movimentacoes_caixa")
        
        return movimentacoes
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar movimentações: {e}")
        logger.error(f"Tipo do erro: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

def obter_saldo_caixa():
    """Calcula o saldo atual do caixa"""
    try:
        logger.info("=== INICIANDO obter_saldo_caixa ===")
        conn = get_db_connection()
        cursor = conn.cursor()
        logger.info("Conexão estabelecida para obter_saldo_caixa")
        
        logger.info("Executando query para calcular saldo...")
        cursor.execute('''
            SELECT 
                COALESCE(SUM(CASE WHEN tipo = 'entrada' THEN valor ELSE 0 END), 0) as total_entradas,
                COALESCE(SUM(CASE WHEN tipo = 'saida' THEN valor ELSE 0 END), 0) as total_saidas
            FROM movimentacoes_caixa
        ''')
        
        resultado = cursor.fetchone()
        logger.info(f"Resultado da query: {resultado}")
        
        if resultado:
            total_entradas = float(resultado[0])
            total_saidas = float(resultado[1])
            saldo = total_entradas - total_saidas
        else:
            logger.warning("Nenhum resultado encontrado, usando valores padrão")
            total_entradas = total_saidas = saldo = 0.0
        
        cursor.close()
        conn.close()
        logger.info("Conexão fechada para obter_saldo_caixa")
        
        resultado_final = {
            'total_entradas': total_entradas,
            'total_saidas': total_saidas,
            'saldo': saldo
        }
        logger.info(f"Saldo calculado com sucesso: {resultado_final}")
        return resultado_final
        
    except Exception as e:
        logger.error(f"❌ Erro ao calcular saldo: {e}")
        logger.error(f"Tipo do erro: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

def obter_comprovantes_movimentacao(movimentacao_id):
    """Obtém os comprovantes de uma movimentação"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute('''
            SELECT id, nome_arquivo, tipo_arquivo, data_upload
            FROM comprovantes_caixa
            WHERE movimentacao_id = %s
            ORDER BY data_upload DESC
        ''', (movimentacao_id,))
        
        comprovantes = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return comprovantes
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter comprovantes: {e}")
        raise

def listar_cadastros_simples():
    """Lista cadastros com apenas ID e nome para selects"""
    try:
        logger.info("=== INICIANDO listar_cadastros_simples ===")
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        logger.info("Conexão estabelecida para listar_cadastros_simples")
        
        logger.info("Executando query para listar cadastros...")
        cursor.execute('''
            SELECT id, nome_completo
            FROM cadastros
            ORDER BY nome_completo
        ''')
        
        cadastros = cursor.fetchall()
        logger.info(f"Cadastros encontrados: {len(cadastros)}")
        
        cursor.close()
        conn.close()
        logger.info("Conexão fechada para listar_cadastros_simples")
        
        return cadastros
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar cadastros simples: {e}")
        logger.error(f"Tipo do erro: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

# Funções para sistema de permissões
def obter_permissoes_usuario(usuario_id):
    """Obtém todas as permissões de um usuário"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT permissao FROM permissoes_usuario 
            WHERE usuario_id = %s
        ''', (usuario_id,))
        
        permissoes = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        
        return permissoes
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter permissões: {e}")
        return []

def adicionar_permissao_usuario(usuario_id, permissao):
    """Adiciona uma permissão a um usuário"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO permissoes_usuario (usuario_id, permissao)
            VALUES (%s, %s)
            ON CONFLICT (usuario_id, permissao) DO NOTHING
        ''', (usuario_id, permissao))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao adicionar permissão: {e}")
        return False

def remover_permissao_usuario(usuario_id, permissao):
    """Remove uma permissão de um usuário"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM permissoes_usuario 
            WHERE usuario_id = %s AND permissao = %s
        ''', (usuario_id, permissao))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao remover permissão: {e}")
        return False

def usuario_tem_permissao(usuario_nome, permissao):
    """Verifica se um usuário tem uma permissão específica"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Admin ID 1 tem permissão total
        cursor.execute('SELECT id FROM usuarios WHERE usuario = %s', (usuario_nome,))
        usuario_data = cursor.fetchone()
        
        if usuario_data and usuario_data[0] == 1:  # Admin ID 1
            cursor.close()
            conn.close()
            return True
        
        # Verificar permissão específica para outros usuários
        cursor.execute('''
            SELECT COUNT(*) FROM permissoes_usuario p
            JOIN usuarios u ON p.usuario_id = u.id
            WHERE u.usuario = %s AND p.permissao = %s
        ''', (usuario_nome, permissao))
        
        tem_permissao = cursor.fetchone()[0] > 0
        cursor.close()
        conn.close()
        
        return tem_permissao
        
    except Exception as e:
        logger.error(f"❌ Erro ao verificar permissão: {e}")
        return False
