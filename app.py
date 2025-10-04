from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, send_from_directory
from database import get_db_connection, init_db_tables, create_admin_user
from db_helper import get_db, execute_query
import csv
import io
import os
import logging
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Configurar logging detalhado
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'ameg_secret_2024_fallback_key_change_in_production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

logger.info("🚀 Iniciando aplicação AMEG")
logger.info(f"RAILWAY_ENVIRONMENT: {os.environ.get('RAILWAY_ENVIRONMENT')}")
logger.info(f"DATABASE_URL presente: {'DATABASE_URL' in os.environ}")
logger.debug(f"SECRET_KEY configurada: {bool(app.secret_key)}")

# Inicializar banco na inicialização (apenas no Railway)
if os.environ.get('RAILWAY_ENVIRONMENT'):
    logger.info("🔧 Iniciando configuração do banco PostgreSQL...")
    try:
        logger.info("🔧 Inicializando tabelas do banco primeiro...")
        logger.debug("Chamando init_db_tables()...")
        init_db_tables()
        logger.info("✅ Tabelas inicializadas")
        
        logger.info("👤 Criando usuário admin...")
        logger.debug("Chamando create_admin_user()...")
        create_admin_user()
        logger.info("✅ Usuário admin configurado")
        
        logger.info("✅ Banco inicializado completamente no Railway")
    except Exception as e:
        logger.error(f"❌ Erro na inicialização do banco: {e}")
        logger.error(f"Tipo do erro: {type(e)}")
        logger.error(f"Args do erro: {e.args}")
        import traceback
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        logger.warning("⚠️ Continuando sem inicialização do banco...")
else:
    logger.info("🏠 Ambiente local detectado - usando SQLite")

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}

# Limites dos campos conforme definido na tabela do banco
FIELD_LIMITS = {
    'nome_completo': 255,
    'numero': 10,
    'bairro': 100,
    'cep': 10,
    'telefone': 20,
    'titulo_eleitor': 20,
    'cidade_titulo': 100,
    'cpf': 14,
    'rg': 20,
    'nis': 20,
    'estado_civil': 30,
    'escolaridade': 100,
    'profissao': 100,
    'nome_companheiro': 255,
    'cpf_companheiro': 14,
    'rg_companheiro': 20,
    'escolaridade_companheiro': 100,
    'profissao_companheiro': 100,
    'titulo_companheiro': 20,
    'cidade_titulo_companheiro': 100,
    'nis_companheiro': 20,
    'tipo_trabalho': 100,
    'casa_tipo': 50,
    'casa_material': 50,
    'energia': 10,
    'lixo': 10,
    'agua': 10,
    'esgoto': 10,
    'tem_doenca_cronica': 10,
    'usa_medicamento_continuo': 10,
    'tem_doenca_mental': 10,
    'tem_deficiencia': 10,
    'precisa_cuidados_especiais': 10,
    'atua_ponto_fixo': 10,
    'trabalho_continuo_temporada': 20,
    'sofreu_acidente_trabalho': 10,
    'trabalho_incomoda_calor': 10,
    'trabalho_incomoda_barulho': 10,
    'trabalho_incomoda_seguranca': 10,
    'trabalho_incomoda_banheiros': 10,
    'trabalho_incomoda_outro': 10,
    'acesso_banheiro_agua': 10,
    'possui_autorizacao_municipal': 10,
    'problemas_fiscalizacao_policia': 10,
    'estrutura_barraca': 10,
    'estrutura_carrinho': 10,
    'estrutura_mesa': 10,
    'estrutura_outro': 10,
    'necessita_energia_eletrica': 10,
    'utiliza_gas_cozinha': 10,
    'usa_veiculo_proprio': 10,
    'fonte_renda_trabalho_ambulante': 10,
    'fonte_renda_aposentadoria': 10,
    'fonte_renda_outro_trabalho': 10,
    'fonte_renda_beneficio_social': 10,
    'fonte_renda_outro': 10
}

def validate_field_lengths(form_data):
    """Valida se os campos não excedem os limites da tabela"""
    errors = []
    
    for field_name, max_length in FIELD_LIMITS.items():
        if field_name in form_data:
            value = str(form_data[field_name]).strip()
            if len(value) > max_length:
                field_display = field_name.replace('_', ' ').title()
                errors.append(f"{field_display}: máximo {max_length} caracteres (atual: {len(value)})")
    
    return errors

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Headers de segurança
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/')
def login():
    if 'usuario' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def fazer_login():
    usuario = request.form['usuario']
    senha = request.form['senha']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # No Railway sempre será PostgreSQL
    cursor.execute('SELECT senha FROM usuarios WHERE usuario = %s', (usuario,))
    
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if user and check_password_hash(user[0], senha):
        session['usuario'] = usuario
        return redirect(url_for('dashboard'))
    else:
        flash('Usuário ou senha incorretos!')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM cadastros')
    total = cursor.fetchone()[0]
    
    cursor.execute('SELECT id, nome_completo, telefone, bairro, data_cadastro FROM cadastros ORDER BY data_cadastro DESC LIMIT 5')
    ultimos = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('dashboard.html', total=total, ultimos=ultimos)

@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    if 'usuario' not in session:
        logger.debug("Usuário não logado tentando acessar /cadastrar")
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        logger.info("🆕 Iniciando novo cadastro...")
        logger.debug(f"Dados recebidos: nome_completo={request.form.get('nome_completo')}")
        
        # Validar limites dos campos
        validation_errors = validate_field_lengths(request.form)
        if validation_errors:
            logger.warning(f"❌ Validação falhou: {len(validation_errors)} erros encontrados")
            for error in validation_errors:
                flash(f"Erro de validação: {error}", 'error')
            return render_template('cadastrar.html')
        
        try:
            conn, db_type = get_db()
            cursor = conn.cursor()
            logger.debug("Conexão com banco estabelecida para cadastro")
            
            # Preparar dados para INSERT - tratar valores vazios para INTEGER
            def safe_int_or_null(value):
                if value == '' or value is None:
                    return None
                try:
                    return int(value)
                except (ValueError, TypeError):
                    return None
            
            def safe_decimal_or_null(value):
                if value == '' or value is None:
                    return None
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return None
            
            dados_insert = (
                request.form.get('nome_completo'), request.form.get('endereco'), request.form.get('numero'),
                request.form.get('bairro'), request.form.get('cep'), request.form.get('cidade'), request.form.get('estado'), request.form.get('telefone'),
                request.form.get('ponto_referencia'), request.form.get('genero'), safe_int_or_null(request.form.get('idade')),
                request.form.get('data_nascimento'), request.form.get('titulo_eleitor'), request.form.get('cidade_titulo'),
                request.form.get('cpf'), request.form.get('rg'), request.form.get('nis'),
                request.form.get('estado_civil'), request.form.get('escolaridade'), request.form.get('profissao'),
                request.form.get('nome_companheiro'), request.form.get('cpf_companheiro'), request.form.get('rg_companheiro'),
                safe_int_or_null(request.form.get('idade_companheiro')), request.form.get('escolaridade_companheiro'), request.form.get('profissao_companheiro'),
                request.form.get('data_nascimento_companheiro'), request.form.get('titulo_companheiro'), request.form.get('cidade_titulo_companheiro'),
                request.form.get('nis_companheiro'), request.form.get('tipo_trabalho'), safe_int_or_null(request.form.get('pessoas_trabalham')),
                safe_int_or_null(request.form.get('aposentados_pensionistas')), safe_int_or_null(request.form.get('num_pessoas_familia')), safe_int_or_null(request.form.get('num_familias')),
                safe_int_or_null(request.form.get('adultos')), safe_int_or_null(request.form.get('criancas')), safe_int_or_null(request.form.get('adolescentes')),
                safe_int_or_null(request.form.get('idosos')), safe_int_or_null(request.form.get('gestantes')), safe_int_or_null(request.form.get('nutrizes')),
                safe_decimal_or_null(request.form.get('renda_familiar')), safe_decimal_or_null(request.form.get('renda_per_capita')), safe_decimal_or_null(request.form.get('bolsa_familia')),
                request.form.get('casa_tipo'), request.form.get('casa_material'), request.form.get('energia'),
                request.form.get('lixo'), request.form.get('agua'), request.form.get('esgoto'),
                request.form.get('observacoes'), request.form.get('tem_doenca_cronica'), request.form.get('doencas_cronicas'),
                request.form.get('usa_medicamento_continuo'), request.form.get('medicamentos_continuos'), request.form.get('tem_doenca_mental'),
                request.form.get('doencas_mentais'), request.form.get('tem_deficiencia'), request.form.get('tipo_deficiencia'),
                request.form.get('precisa_cuidados_especiais'), request.form.get('cuidados_especiais'),
                # Novos campos de trabalho
                request.form.get('com_que_trabalha'), request.form.get('onde_trabalha'), request.form.get('localizacao_trabalho'), request.form.get('horario_trabalho'),
                request.form.get('tempo_atividade'), request.form.get('atua_ponto_fixo'), request.form.get('qual_ponto_fixo'),
                safe_int_or_null(request.form.get('dias_semana_trabalha')), request.form.get('trabalho_continuo_temporada'),
                request.form.get('sofreu_acidente_trabalho'), request.form.get('qual_acidente'),
                request.form.get('trabalho_incomoda_calor'), request.form.get('trabalho_incomoda_barulho'),
                request.form.get('trabalho_incomoda_seguranca'), request.form.get('trabalho_incomoda_banheiros'),
                request.form.get('trabalho_incomoda_outro'), request.form.get('trabalho_incomoda_outro_desc'),
                request.form.get('acesso_banheiro_agua'), safe_int_or_null(request.form.get('trabalha_sozinho_ajudantes')),
                request.form.get('possui_autorizacao_municipal'), request.form.get('problemas_fiscalizacao_policia'),
                request.form.get('estrutura_barraca'), request.form.get('estrutura_carrinho'),
                request.form.get('estrutura_mesa'), request.form.get('estrutura_outro'), request.form.get('estrutura_outro_desc'),
                request.form.get('necessita_energia_eletrica'), request.form.get('utiliza_gas_cozinha'),
                request.form.get('usa_veiculo_proprio'), request.form.get('qual_veiculo'),
                request.form.get('fonte_renda_trabalho_ambulante'), request.form.get('fonte_renda_aposentadoria'),
                request.form.get('fonte_renda_outro_trabalho'), request.form.get('fonte_renda_beneficio_social'),
                request.form.get('fonte_renda_outro'), request.form.get('fonte_renda_outro_desc'),
                safe_int_or_null(request.form.get('pessoas_dependem_renda'))
            )
            
            logger.debug(f"📊 Preparando INSERT com {len(dados_insert)} valores")
            logger.debug(f"🔍 Primeiros 5 valores: {dados_insert[:5]}")
            logger.debug(f"🔍 Últimos 5 valores: {dados_insert[-5:]}")
            
            logger.debug("Executando INSERT para novo cadastro...")
            execute_query("""INSERT INTO cadastros (
            nome_completo, endereco, numero, bairro, cep, cidade, estado, telefone, ponto_referencia, genero, idade,
            data_nascimento, titulo_eleitor, cidade_titulo, cpf, rg, nis, estado_civil,
            escolaridade, profissao, nome_companheiro, cpf_companheiro, rg_companheiro,
            idade_companheiro, escolaridade_companheiro, profissao_companheiro, data_nascimento_companheiro,
            titulo_companheiro, cidade_titulo_companheiro, nis_companheiro, tipo_trabalho,
            pessoas_trabalham, aposentados_pensionistas, num_pessoas_familia, num_familias,
            adultos, criancas, adolescentes, idosos, gestantes, nutrizes, renda_familiar,
            renda_per_capita, bolsa_familia, casa_tipo, casa_material, energia, lixo, agua,
            esgoto, observacoes, tem_doenca_cronica, doencas_cronicas, usa_medicamento_continuo,
            medicamentos_continuos, tem_doenca_mental, doencas_mentais, tem_deficiencia,
            tipo_deficiencia, precisa_cuidados_especiais, cuidados_especiais,
            com_que_trabalha, onde_trabalha, localizacao_trabalho, horario_trabalho, tempo_atividade, atua_ponto_fixo,
            qual_ponto_fixo, dias_semana_trabalha, trabalho_continuo_temporada, sofreu_acidente_trabalho,
            qual_acidente, trabalho_incomoda_calor, trabalho_incomoda_barulho, trabalho_incomoda_seguranca,
            trabalho_incomoda_banheiros, trabalho_incomoda_outro, trabalho_incomoda_outro_desc,
            acesso_banheiro_agua, trabalha_sozinho_ajudantes, possui_autorizacao_municipal,
            problemas_fiscalizacao_policia, estrutura_barraca, estrutura_carrinho, estrutura_mesa,
            estrutura_outro, estrutura_outro_desc, necessita_energia_eletrica, utiliza_gas_cozinha,
            usa_veiculo_proprio, qual_veiculo, fonte_renda_trabalho_ambulante, fonte_renda_aposentadoria,
            fonte_renda_outro_trabalho, fonte_renda_beneficio_social, fonte_renda_outro,
            fonte_renda_outro_desc, pessoas_dependem_renda
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            dados_insert)
            
            logger.info("✅ INSERT executado com sucesso!")
        
            # Para obter o ID do cadastro inserido, usar a mesma conexão
            logger.debug("🔍 Buscando ID do cadastro inserido...")
            
            if db_type == 'postgresql':
                cursor.execute('SELECT id FROM cadastros ORDER BY id DESC LIMIT 1')
            else:
                cursor.execute('SELECT last_insert_rowid()')
            
            result = cursor.fetchone()
            if result:
                # FIXED: Handle PostgreSQL dict vs SQLite tuple results
                if hasattr(result, 'keys'):  # PostgreSQL RealDictCursor
                    cadastro_id = result['id']
                else:  # SQLite Row or tuple
                    cadastro_id = result[0]
                logger.debug(f"ID do cadastro inserido: {cadastro_id}")
            else:
                cadastro_id = None
                logger.error("❌ Não foi possível obter o ID do cadastro inserido")
            
            # Upload de arquivos usando a mesma conexão
            uploaded_files = []
            if cadastro_id:
                for file_key in ['laudo', 'receita', 'imagem']:
                    if file_key in request.files:
                        file = request.files[file_key]
                        if file and file.filename and allowed_file(file.filename):
                            logger.debug(f"Processando arquivo: {file.filename} ({file_key})")
                            file_data = file.read()
                            descricao = request.form.get(f'descricao_{file_key}', '')
                            
                            if db_type == 'postgresql':
                                cursor.execute('INSERT INTO arquivos_saude (cadastro_id, nome_arquivo, tipo_arquivo, arquivo_dados, descricao) VALUES (%s, %s, %s, %s, %s)', 
                                            (cadastro_id, file.filename, file_key, file_data, descricao))
                            else:
                                cursor.execute('INSERT INTO arquivos_saude (cadastro_id, nome_arquivo, tipo_arquivo, arquivo_dados, descricao) VALUES (?, ?, ?, ?, ?)', 
                                            (cadastro_id, file.filename, file_key, file_data, descricao))
                            
                            uploaded_files.append(file_key)
                            logger.debug(f"Arquivo {file.filename} salvo com sucesso")
            
            conn.commit()
            conn.close()
            logger.info("✅ Cadastro e arquivos salvos com sucesso no banco")
            
            if uploaded_files:
                logger.info(f"📎 Arquivos enviados: {', '.join(uploaded_files)}")
                flash(f'Cadastro realizado com sucesso! Arquivos enviados: {", ".join(uploaded_files)}')
            else:
                flash('Cadastro realizado com sucesso!')
            return redirect(url_for('dashboard'))
        
        except Exception as e:
            logger.error(f"❌ Erro ao salvar cadastro: {e}")
            logger.error(f"Tipo do erro: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            flash('Erro ao salvar cadastro. Tente novamente.')
            return redirect(url_for('cadastrar'))
    
    return render_template('cadastrar.html')

@app.route('/relatorios')
def relatorios():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('tipos_relatorios.html')

@app.route('/relatorio_completo')
def relatorio_completo():
    logger.info("🔍 INICIANDO relatorio_completo")
    
    if 'usuario' not in session:
        logger.warning("⚠️ Usuário não logado tentando acessar relatorio_completo")
        return redirect(url_for('login'))
    
    try:
        logger.info("📊 Obtendo conexão com banco de dados...")
        conn = get_db_connection()
        cursor = conn.cursor()
        logger.info("✅ Conexão estabelecida")
        
        logger.info("🔍 Executando query SELECT * FROM cadastros...")
        cursor.execute('SELECT * FROM cadastros ORDER BY nome_completo')
        logger.info("✅ Query executada com sucesso")
        
        logger.info("📋 Fazendo fetchall()...")
        cadastros = cursor.fetchall()
        logger.info(f"✅ Dados obtidos: {len(cadastros)} registros encontrados")
        
        if cadastros:
            logger.info(f"🔍 Primeiro registro: tipo={type(cadastros[0])}")
            logger.info(f"🔍 Primeiro registro length: {len(cadastros[0]) if cadastros[0] else 'None'}")
            logger.info(f"🔍 Primeiros 5 campos do primeiro registro: {cadastros[0][:5] if len(cadastros[0]) > 5 else cadastros[0]}")
        
        cursor.close()
        conn.close()
        logger.info("✅ Conexão fechada")
        
        logger.info("🎨 Renderizando template relatorio_completo.html...")
        return render_template('relatorio_completo.html', cadastros=cadastros)
        
    except Exception as e:
        logger.error(f"❌ ERRO em relatorio_completo: {str(e)}")
        logger.error(f"❌ Tipo do erro: {type(e)}")
        import traceback
        logger.error(f"❌ Traceback completo: {traceback.format_exc()}")
        
        # Tentar fechar conexões se existirem
        try:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
        except:
            pass
            
        flash('Erro ao carregar relatório completo. Verifique os logs.')
        return redirect(url_for('relatorios'))

@app.route('/relatorio_simplificado')
def relatorio_simplificado():
    logger.info("🔍 INICIANDO relatorio_simplificado")
    
    if 'usuario' not in session:
        logger.warning("⚠️ Usuário não logado tentando acessar relatorio_simplificado")
        return redirect(url_for('login'))
    
    try:
        logger.info("📊 Obtendo conexão com banco de dados...")
        conn = get_db_connection()
        cursor = conn.cursor()
        logger.info("✅ Conexão estabelecida")
        
        query = 'SELECT nome_completo, telefone, bairro, renda_familiar FROM cadastros ORDER BY nome_completo'
        logger.info(f"🔍 Executando query: {query}")
        cursor.execute(query)
        logger.info("✅ Query executada com sucesso")
        
        cadastros = cursor.fetchall()
        logger.info(f"✅ Dados obtidos: {len(cadastros)} registros encontrados")
        
        if cadastros:
            logger.info(f"🔍 Primeiro registro: {cadastros[0]}")
        
        cursor.close()
        conn.close()
        logger.info("✅ Conexão fechada")
        
        logger.info("🎨 Renderizando template relatorio_simplificado.html...")
        return render_template('relatorio_simplificado.html', cadastros=cadastros)
        
    except Exception as e:
        logger.error(f"❌ ERRO em relatorio_simplificado: {str(e)}")
        logger.error(f"❌ Tipo do erro: {type(e)}")
        import traceback
        logger.error(f"❌ Traceback completo: {traceback.format_exc()}")
        
        try:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
        except:
            pass
            
        flash('Erro ao carregar relatório simplificado. Verifique os logs.')
        return redirect(url_for('relatorios'))

@app.route('/relatorio_estatistico')
def relatorio_estatistico():
    logger.info("🔍 INICIANDO relatorio_estatistico")
    
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        logger.info("✅ Conexão estabelecida para estatístico")
        
        # Estatísticas gerais
        cursor.execute('SELECT COUNT(*) FROM cadastros')
        total = cursor.fetchone()[0]
        logger.info(f"📊 Total de cadastros: {total}")
        
        # Por bairro
        cursor.execute('SELECT bairro, COUNT(*) FROM cadastros GROUP BY bairro ORDER BY COUNT(*) DESC')
        por_bairro = cursor.fetchall()
        logger.info(f"📊 Bairros encontrados: {len(por_bairro)}")
        
        # Por gênero
        cursor.execute('SELECT genero, COUNT(*) FROM cadastros GROUP BY genero')
        por_genero = cursor.fetchall()
        logger.info(f"📊 Gêneros encontrados: {len(por_genero)}")
        
        # Por faixa etária
        cursor.execute('''SELECT 
            CASE 
                WHEN idade < 18 THEN 'Menor de 18'
                WHEN idade BETWEEN 18 AND 30 THEN '18-30 anos'
                WHEN idade BETWEEN 31 AND 50 THEN '31-50 anos'
                WHEN idade BETWEEN 51 AND 65 THEN '51-65 anos'
                ELSE 'Acima de 65'
            END as faixa_etaria,
            COUNT(*) 
            FROM cadastros 
            WHERE idade IS NOT NULL 
            GROUP BY faixa_etaria''')
        por_idade = cursor.fetchall()
        logger.info(f"📊 Faixas etárias encontradas: {len(por_idade)}")
        
        cursor.close()
        conn.close()
        
        stats = {
            'total': total,
            'por_bairro': por_bairro,
            'por_genero': por_genero,
            'por_idade': por_idade
        }
        
        logger.info("✅ Dados estatísticos preparados com sucesso")
        return render_template('relatorio_estatistico.html', stats=stats)
        
    except Exception as e:
        logger.error(f"❌ ERRO em relatorio_estatistico: {str(e)}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        flash('Erro ao carregar relatório estatístico.')
        return redirect(url_for('relatorios'))

@app.route('/relatorio_por_bairro')
def relatorio_por_bairro():
    logger.info("🔍 INICIANDO relatorio_por_bairro")
    
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        logger.info("✅ Conexão estabelecida para relatório por bairro")
        
        query = '''SELECT bairro, COUNT(*) as total, 
                   AVG(CASE WHEN renda_familiar ~ '^[0-9]+\.?[0-9]*$' THEN renda_familiar::numeric ELSE NULL END) as renda_media
                   FROM cadastros 
                   WHERE bairro IS NOT NULL 
                   GROUP BY bairro 
                   ORDER BY total DESC'''
        logger.info(f"🔍 Executando query: {query}")
        cursor.execute(query)
        
        bairros = cursor.fetchall()
        logger.info(f"✅ Bairros encontrados: {len(bairros)}")
        
        if bairros:
            logger.info(f"🔍 Primeiro bairro: {bairros[0]}")
        
        cursor.close()
        conn.close()
        
        return render_template('relatorio_por_bairro.html', bairros=bairros)
        
    except Exception as e:
        logger.error(f"❌ ERRO em relatorio_por_bairro: {str(e)}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        flash('Erro ao carregar relatório por bairro.')
        return redirect(url_for('relatorios'))

@app.route('/relatorio_renda')
def relatorio_renda():
    logger.info("🔍 INICIANDO relatorio_renda")
    
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        logger.info("✅ Conexão estabelecida para relatório de renda")
        
        # Faixas de renda - corrigido para PostgreSQL
        query1 = '''SELECT 
            CASE 
                WHEN renda_familiar ~ '^[0-9]+\.?[0-9]*$' AND renda_familiar::numeric <= 1000 THEN 'Até R$ 1.000'
                WHEN renda_familiar ~ '^[0-9]+\.?[0-9]*$' AND renda_familiar::numeric BETWEEN 1001 AND 2000 THEN 'R$ 1.001 - R$ 2.000'
                WHEN renda_familiar ~ '^[0-9]+\.?[0-9]*$' AND renda_familiar::numeric BETWEEN 2001 AND 3000 THEN 'R$ 2.001 - R$ 3.000'
                WHEN renda_familiar ~ '^[0-9]+\.?[0-9]*$' AND renda_familiar::numeric > 3000 THEN 'Acima de R$ 3.000'
                ELSE 'Não informado'
            END as faixa_renda,
            COUNT(*) 
            FROM cadastros 
            GROUP BY faixa_renda'''
        logger.info(f"🔍 Executando query faixas de renda: {query1}")
        cursor.execute(query1)
        faixas_renda = cursor.fetchall()
        logger.info(f"✅ Faixas de renda encontradas: {len(faixas_renda)}")
        
        # Renda por bairro - corrigido para PostgreSQL
        query2 = '''SELECT bairro, 
                     AVG(CASE WHEN renda_familiar ~ '^[0-9]+\.?[0-9]*$' THEN renda_familiar::numeric ELSE NULL END) as renda_media, 
                     COUNT(*) as total
                     FROM cadastros 
                     WHERE bairro IS NOT NULL
                     GROUP BY bairro 
                     ORDER BY renda_media DESC NULLS LAST'''
        logger.info(f"🔍 Executando query renda por bairro: {query2}")
        cursor.execute(query2)
        renda_bairro = cursor.fetchall()
        logger.info(f"✅ Renda por bairro encontrada: {len(renda_bairro)}")
        
        cursor.close()
        conn.close()
        
        return render_template('relatorio_renda.html', faixas_renda=faixas_renda, renda_bairro=renda_bairro)
        
    except Exception as e:
        logger.error(f"❌ ERRO em relatorio_renda: {str(e)}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        flash('Erro ao carregar relatório de renda.')
        return redirect(url_for('relatorios'))

@app.route('/relatorio_saude')
def relatorio_saude():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    c = cursor = conn[0].cursor() if isinstance(conn, tuple) else conn.cursor()
    
    c.execute('SELECT COUNT(*) FROM cadastros WHERE tem_doenca_cronica = %s', ('Sim',))
    com_doenca_cronica = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM cadastros WHERE usa_medicamento_continuo = %s', ('Sim',))
    usa_medicamento = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM cadastros WHERE tem_doenca_mental = %s', ('Sim',))
    com_doenca_mental = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM cadastros WHERE tem_deficiencia = %s', ('Sim',))
    com_deficiencia = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM cadastros WHERE precisa_cuidados_especiais = %s', ('Sim',))
    precisa_cuidados = c.fetchone()[0]
    
    c.execute("""SELECT id, nome_completo, idade, telefone, bairro, tem_doenca_cronica, doencas_cronicas,
                usa_medicamento_continuo, medicamentos_continuos, tem_doenca_mental, doencas_mentais,
                tem_deficiencia, tipo_deficiencia, precisa_cuidados_especiais, cuidados_especiais
                FROM cadastros 
                WHERE tem_doenca_cronica = %s OR usa_medicamento_continuo = %s 
                OR tem_doenca_mental = %s OR tem_deficiencia = %s 
                OR precisa_cuidados_especiais = %s
                ORDER BY nome_completo""", ('Sim', 'Sim', 'Sim', 'Sim', 'Sim'))
    cadastros_saude = c.fetchall()
    
    conn.close()
    
    stats = {
        'com_doenca_cronica': com_doenca_cronica,
        'usa_medicamento': usa_medicamento,
        'com_doenca_mental': com_doenca_mental,
        'com_deficiencia': com_deficiencia,
        'precisa_cuidados': precisa_cuidados
    }
    
    return render_template('relatorio_saude.html', stats=stats, cadastros=cadastros_saude)

@app.route('/exportar')
def exportar():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    tipo = request.args.get('tipo', 'completo')
    formato = request.args.get('formato', 'csv')
    cadastro_id = request.args.get('cadastro_id')  # Para exportar cadastro individual
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if tipo == 'completo':
        if cadastro_id:
            cursor.execute('SELECT * FROM cadastros WHERE id = %s', (cadastro_id,))
            dados = cursor.fetchall()
            filename = f'cadastro_{cadastro_id}'
        else:
            cursor.execute('SELECT * FROM cadastros ORDER BY nome_completo')
            dados = cursor.fetchall()
            filename = 'relatorio_completo'
    elif tipo == 'simplificado':
        cursor.execute('SELECT nome_completo, telefone, bairro, renda_familiar FROM cadastros ORDER BY nome_completo')
        dados = cursor.fetchall()
        filename = 'relatorio_simplificado'
    elif tipo == 'saude':
        cursor.execute('''SELECT nome_completo, idade, telefone, bairro, tem_doenca_cronica, doencas_cronicas,
                         usa_medicamento_continuo, medicamentos_continuos, tem_doenca_mental, doencas_mentais,
                         tem_deficiencia, tipo_deficiencia FROM cadastros 
                         WHERE tem_doenca_cronica = %s OR usa_medicamento_continuo = %s 
                         OR tem_doenca_mental = %s OR tem_deficiencia = %s
                         ORDER BY nome_completo''', ('Sim', 'Sim', 'Sim', 'Sim'))
        dados = cursor.fetchall()
        filename = 'relatorio_saude'
    elif tipo == 'estatistico':
        # Buscar todas as estatísticas como no relatório web
        cursor.execute('SELECT COUNT(*) FROM cadastros')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT bairro, COUNT(*) FROM cadastros WHERE bairro IS NOT NULL GROUP BY bairro ORDER BY COUNT(*) DESC')
        por_bairro = cursor.fetchall()
        
        cursor.execute('SELECT genero, COUNT(*) FROM cadastros WHERE genero IS NOT NULL GROUP BY genero ORDER BY COUNT(*) DESC')
        por_genero = cursor.fetchall()
        
        cursor.execute('''SELECT 
            CASE 
                WHEN idade < 18 THEN 'Menor de 18 anos'
                WHEN idade BETWEEN 18 AND 30 THEN '18-30 anos'
                WHEN idade BETWEEN 31 AND 50 THEN '31-50 anos'
                WHEN idade BETWEEN 51 AND 65 THEN '51-65 anos'
                ELSE 'Acima de 65 anos'
            END as faixa_etaria,
            COUNT(*) 
            FROM cadastros 
            WHERE idade IS NOT NULL 
            GROUP BY faixa_etaria''')
        por_idade = cursor.fetchall()
        
        # Combinar todos os dados para exportação
        dados = {
            'total': total,
            'por_bairro': por_bairro,
            'por_genero': por_genero,
            'por_idade': por_idade
        }
        filename = 'relatorio_estatistico'
    elif tipo == 'bairro':
        cursor.execute('''SELECT bairro, COUNT(*) as total, 
                         AVG(CASE WHEN renda_familiar ~ '^[0-9]+\.?[0-9]*$' THEN renda_familiar::numeric ELSE NULL END) as renda_media
                         FROM cadastros 
                         WHERE bairro IS NOT NULL 
                         GROUP BY bairro 
                         ORDER BY total DESC''')
        dados = cursor.fetchall()
        filename = 'relatorio_por_bairro'
    elif tipo == 'renda':
        cursor.execute('''SELECT bairro, 
                         AVG(CASE WHEN renda_familiar ~ '^[0-9]+\.?[0-9]*$' THEN renda_familiar::numeric ELSE NULL END) as renda_media, 
                         COUNT(*) as total
                         FROM cadastros 
                         WHERE bairro IS NOT NULL
                         GROUP BY bairro 
                         ORDER BY renda_media DESC NULLS LAST''')
        dados = cursor.fetchall()
        filename = 'relatorio_renda'
    else:
        cursor.execute('SELECT * FROM cadastros ORDER BY nome_completo')
        dados = cursor.fetchall()
        filename = 'relatorio_geral'
    
    cursor.close()
    conn.close()
    
    if formato == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Cabeçalhos baseados no tipo
        if tipo == 'simplificado':
            writer.writerow(['Nome', 'Telefone', 'Bairro', 'Renda Familiar'])
        elif tipo == 'saude':
            writer.writerow(['Nome', 'Idade', 'Telefone', 'Bairro', 'Doença Crônica', 'Doenças', 
                           'Medicamento Contínuo', 'Medicamentos', 'Doença Mental', 'Doenças Mentais',
                           'Deficiência', 'Tipo Deficiência'])
        elif tipo == 'estatistico':
            writer.writerow(['=== RELATÓRIO ESTATÍSTICO COMPLETO ==='])
            writer.writerow([''])
            writer.writerow(['TOTAL DE CADASTROS:', dados['total']])
            writer.writerow([''])
            writer.writerow(['=== POR BAIRRO ==='])
            writer.writerow(['Bairro', 'Total'])
            for row in dados['por_bairro']:
                writer.writerow([row[0] or 'Não informado', row[1]])
            writer.writerow([''])
            writer.writerow(['=== POR GÊNERO ==='])
            writer.writerow(['Gênero', 'Total'])
            for row in dados['por_genero']:
                writer.writerow([row[0] or 'Não informado', row[1]])
            writer.writerow([''])
            writer.writerow(['=== POR FAIXA ETÁRIA ==='])
            writer.writerow(['Faixa Etária', 'Total'])
            for row in dados['por_idade']:
                writer.writerow([row[0] or 'Não informado', row[1]])
        elif tipo == 'bairro':
            writer.writerow(['Bairro', 'Total de Cadastros', 'Renda Média'])
        elif tipo == 'renda':
            writer.writerow(['Bairro', 'Renda Média', 'Total de Cadastros'])
        else:
            # Cabeçalhos completos 
            writer.writerow(['Nome', 'Telefone', 'Endereço', 'Número', 'Bairro', 'CEP', 'Gênero', 'Idade', 'CPF', 'RG', 'Estado Civil', 'Escolaridade', 'Renda Familiar'])
        
        # Dados
        for row in dados:
            if tipo == 'completo':
                # Usar índices corretos baseados na estrutura da tabela
                row_data = [
                    row[1] if hasattr(row, '__getitem__') else getattr(row, 'nome_completo', ''),  # nome_completo
                    row[6] if hasattr(row, '__getitem__') else getattr(row, 'telefone', ''),      # telefone
                    row[2] if hasattr(row, '__getitem__') else getattr(row, 'endereco', ''),      # endereco
                    row[3] if hasattr(row, '__getitem__') else getattr(row, 'numero', ''),        # numero
                    row[4] if hasattr(row, '__getitem__') else getattr(row, 'bairro', ''),        # bairro
                    row[5] if hasattr(row, '__getitem__') else getattr(row, 'cep', ''),           # cep
                    row[8] if hasattr(row, '__getitem__') else getattr(row, 'genero', ''),        # genero
                    row[9] if hasattr(row, '__getitem__') else getattr(row, 'idade', ''),         # idade
                    row[13] if hasattr(row, '__getitem__') else getattr(row, 'cpf', ''),          # cpf
                    row[14] if hasattr(row, '__getitem__') else getattr(row, 'rg', ''),           # rg
                    row[16] if hasattr(row, '__getitem__') else getattr(row, 'estado_civil', ''), # estado_civil
                    row[17] if hasattr(row, '__getitem__') else getattr(row, 'escolaridade', ''), # escolaridade
                    row[40] if hasattr(row, '__getitem__') else getattr(row, 'renda_familiar', '') # renda_familiar
                ]
            elif tipo in ['bairro', 'renda']:
                row_data = [
                    str(row[0] or 'Não informado'),
                    f'{row[1]:.2f}' if row[1] and len(row) > 2 else str(row[1] or ''),
                    str(row[2]) if len(row) > 2 else ''
                ]
            elif tipo == 'simplificado':
                row_data = list(row)
            elif tipo == 'saude':
                row_data = list(row)
            else:
                row_data = list(row)
            writer.writerow(row_data)
        
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'{filename}.csv'
        )
    
    # Para PDF, usar ReportLab
    elif formato == 'pdf':
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        # Título
        if tipo == 'completo':
            title = Paragraph("AMEG - Relatório Completo de Cadastros", styles['Title'])
        elif tipo == 'simplificado':
            title = Paragraph("AMEG - Relatório Simplificado", styles['Title'])
        elif tipo == 'saude':
            title = Paragraph("AMEG - Relatório de Saúde", styles['Title'])
        elif tipo == 'estatistico':
            title = Paragraph("AMEG - Relatório Estatístico", styles['Title'])
        elif tipo == 'bairro':
            title = Paragraph("AMEG - Relatório por Bairro", styles['Title'])
        elif tipo == 'renda':
            title = Paragraph("AMEG - Relatório de Renda por Bairro", styles['Title'])
        else:
            title = Paragraph("AMEG - Relatório Geral", styles['Title'])
        
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        # Dados da tabela
        if tipo == 'simplificado':
            table_data = [['Nome', 'Telefone', 'Bairro', 'Renda']]
            for row in dados:
                table_data.append([
                    str(row[0] or ''),
                    str(row[1] or ''),
                    str(row[2] or ''),
                    f"R$ {row[3] or '0'}" if row[3] else 'Não informado'
                ])
        elif tipo == 'saude':
            table_data = [['Nome', 'Idade', 'Telefone', 'Bairro', 'Doença Crônica', 'Medicamento']]
            for row in dados:
                table_data.append([
                    str(row[0] or ''),
                    str(row[1] or ''),
                    str(row[2] or ''),
                    str(row[3] or ''),
                    str(row[4] or ''),
                    str(row[6] or '')
                ])
        elif tipo == 'estatistico':
            # Criar múltiplas tabelas para o relatório estatístico completo
            from reportlab.platypus import Paragraph, Spacer
            
            # Total
            total_para = Paragraph(f"<b>Total de Cadastros: {dados['total']}</b>", styles['Heading2'])
            elements.append(total_para)
            elements.append(Spacer(1, 12))
            
            # Tentar criar gráficos de pizza, se falhar usar apenas tabelas
            try:
                from reportlab.graphics.shapes import Drawing
                from reportlab.graphics.charts.piecharts import Pie
                from reportlab.lib import colors as rl_colors
                
                # Por Bairro com gráfico
                bairro_para = Paragraph("<b>📍 Por Bairro</b>", styles['Heading3'])
                elements.append(bairro_para)
                elements.append(Spacer(1, 6))
                
                # Gráfico de pizza
                drawing = Drawing(200, 150)
                pie = Pie()
                pie.x = 50
                pie.y = 25
                pie.width = 100
                pie.height = 100
                pie.data = [row[1] for row in dados['por_bairro'][:6]]  # Limitar a 6 itens
                pie.labels = [str(row[0] or 'N/A')[:10] for row in dados['por_bairro'][:6]]  # Limitar texto
                
                # Cores simples
                pie_colors = [rl_colors.blue, rl_colors.red, rl_colors.green, rl_colors.orange, rl_colors.purple, rl_colors.brown]
                for i in range(len(pie.data)):
                    pie.slices[i].fillColor = pie_colors[i % len(pie_colors)]
                
                drawing.add(pie)
                elements.append(drawing)
                elements.append(Spacer(1, 10))
                
                # Tabela de dados
                table_data = [['Bairro', 'Total']]
                for row in dados['por_bairro']:
                    table_data.append([str(row[0] or 'Não informado'), str(row[1])])
                
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(table)
                elements.append(Spacer(1, 20))
                
                # Por Gênero com gráfico
                genero_para = Paragraph("<b>👥 Por Gênero</b>", styles['Heading3'])
                elements.append(genero_para)
                elements.append(Spacer(1, 6))
                
                drawing2 = Drawing(200, 150)
                pie2 = Pie()
                pie2.x = 50
                pie2.y = 25
                pie2.width = 100
                pie2.height = 100
                pie2.data = [row[1] for row in dados['por_genero']]
                pie2.labels = [str(row[0] or 'N/A') for row in dados['por_genero']]
                
                for i in range(len(pie2.data)):
                    pie2.slices[i].fillColor = pie_colors[i % len(pie_colors)]
                
                drawing2.add(pie2)
                elements.append(drawing2)
                elements.append(Spacer(1, 10))
                
                table_data = [['Gênero', 'Total']]
                for row in dados['por_genero']:
                    table_data.append([str(row[0] or 'Não informado'), str(row[1])])
                
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(table)
                elements.append(Spacer(1, 20))
                
                # Por Idade com gráfico
                idade_para = Paragraph("<b>🎂 Por Faixa Etária</b>", styles['Heading3'])
                elements.append(idade_para)
                elements.append(Spacer(1, 6))
                
                drawing3 = Drawing(200, 150)
                pie3 = Pie()
                pie3.x = 50
                pie3.y = 25
                pie3.width = 100
                pie3.height = 100
                pie3.data = [row[1] for row in dados['por_idade']]
                pie3.labels = [str(row[0] or 'N/A')[:15] for row in dados['por_idade']]
                
                for i in range(len(pie3.data)):
                    pie3.slices[i].fillColor = pie_colors[i % len(pie_colors)]
                
                drawing3.add(pie3)
                elements.append(drawing3)
                elements.append(Spacer(1, 10))
                
                table_data = [['Faixa Etária', 'Total']]
                for row in dados['por_idade']:
                    table_data.append([str(row[0] or 'Não informado'), str(row[1])])
                
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(table)
                
            except Exception as e:
                # Se gráficos falharem, usar apenas tabelas
                logger.error(f"Erro ao criar gráficos PDF: {e}")
                
                # Por Bairro - apenas tabela
                bairro_para = Paragraph("<b>📍 Por Bairro</b>", styles['Heading3'])
                elements.append(bairro_para)
                elements.append(Spacer(1, 6))
                
                table_data = [['Bairro', 'Total']]
                for row in dados['por_bairro']:
                    table_data.append([str(row[0] or 'Não informado'), str(row[1])])
                
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(table)
                elements.append(Spacer(1, 20))
                
                # Por Gênero - apenas tabela
                genero_para = Paragraph("<b>👥 Por Gênero</b>", styles['Heading3'])
                elements.append(genero_para)
                elements.append(Spacer(1, 6))
                
                table_data = [['Gênero', 'Total']]
                for row in dados['por_genero']:
                    table_data.append([str(row[0] or 'Não informado'), str(row[1])])
                
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(table)
                elements.append(Spacer(1, 20))
                
                # Por Idade - apenas tabela
                idade_para = Paragraph("<b>🎂 Por Faixa Etária</b>", styles['Heading3'])
                elements.append(idade_para)
                elements.append(Spacer(1, 6))
                
                table_data = [['Faixa Etária', 'Total']]
                for row in dados['por_idade']:
                    table_data.append([str(row[0] or 'Não informado'), str(row[1])])
                
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(table)
        elif tipo == 'bairro':
            table_data = [['Bairro', 'Total de Cadastros', 'Renda Média']]
            for row in dados:
                table_data.append([
                    str(row[0] or 'Não informado'),
                    str(row[1] or '0'),
                    f"R$ {row[2]:.2f}" if row[2] else 'Não informado'
                ])
        elif tipo == 'renda':
            table_data = [['Bairro', 'Renda Média', 'Total de Cadastros']]
            for row in dados:
                table_data.append([
                    str(row[0] or 'Não informado'),
                    f"R$ {row[1]:.2f}" if row[1] else 'Não informado',
                    str(row[2] or '0')
                ])
        else:  # completo
            if cadastro_id:
                # PDF detalhado para um cadastro específico com TODOS os campos
                for row in dados:
                    # Título do cadastro
                    nome_para = Paragraph(f"<b>Cadastro: {row[1] or 'Não informado'}</b>", styles['Heading2'])
                    elements.append(nome_para)
                    elements.append(Spacer(1, 12))
                    
                    # Dados Pessoais
                    pessoais_para = Paragraph("<b>📋 Dados Pessoais</b>", styles['Heading3'])
                    elements.append(pessoais_para)
                    elements.append(Spacer(1, 6))
                    
                    pessoais_data = [
                        ['Nome Completo:', str(row[1] or '')],
                        ['Endereço:', f"{row[2] or ''}, {row[3] or ''}"],
                        ['Bairro:', str(row[4] or '')],
                        ['CEP:', str(row[5] or '')],
                        ['Telefone:', str(row[6] or '')],
                        ['Ponto Referência:', str(row[7] or '')],
                        ['Gênero:', str(row[8] or '')],
                        ['Idade:', str(row[9] or '')],
                        ['Data Nascimento:', str(row[10] or '')],
                        ['Título Eleitor:', str(row[11] or '')],
                        ['Cidade Título:', str(row[12] or '')],
                        ['CPF:', str(row[13] or '')],
                        ['RG:', str(row[14] or '')],
                        ['NIS:', str(row[15] or '')],
                        ['Estado Civil:', str(row[16] or '')],
                        ['Escolaridade:', str(row[17] or '')],
                        ['Profissão:', str(row[18] or '')]
                    ]
                    
                    pessoais_table = Table(pessoais_data, colWidths=[120, 350])
                    pessoais_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    elements.append(pessoais_table)
                    elements.append(Spacer(1, 15))
                    
                    # Dados do Companheiro
                    if row[19]:  # Se tem companheiro
                        comp_para = Paragraph("<b>💑 Dados do Companheiro(a)</b>", styles['Heading3'])
                        elements.append(comp_para)
                        elements.append(Spacer(1, 6))
                        
                        comp_data = [
                            ['Nome Companheiro:', str(row[19] or '')],
                            ['CPF Companheiro:', str(row[20] or '')],
                            ['RG Companheiro:', str(row[21] or '')],
                            ['Idade Companheiro:', str(row[22] or '')],
                            ['Escolaridade Companheiro:', str(row[23] or '')],
                            ['Profissão Companheiro:', str(row[24] or '')],
                            ['Data Nasc. Companheiro:', str(row[25] or '')],
                            ['Título Companheiro:', str(row[26] or '')],
                            ['Cidade Título Comp.:', str(row[27] or '')],
                            ['NIS Companheiro:', str(row[28] or '')]
                        ]
                        
                        comp_table = Table(comp_data, colWidths=[120, 350])
                        comp_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, -1), 8),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black)
                        ]))
                        elements.append(comp_table)
                        elements.append(Spacer(1, 15))
                    
                    # Dados Familiares e Trabalho
                    familia_para = Paragraph("<b>👨‍👩‍👧‍👦 Dados Familiares e Trabalho</b>", styles['Heading3'])
                    elements.append(familia_para)
                    elements.append(Spacer(1, 6))
                    
                    familia_data = [
                        ['Tipo Trabalho:', str(row[29] or '')],
                        ['Pessoas Trabalham:', str(row[30] or '')],
                        ['Aposentados/Pensionistas:', str(row[31] or '')],
                        ['Pessoas na Família:', str(row[32] or '')],
                        ['Número Famílias:', str(row[33] or '')],
                        ['Adultos:', str(row[34] or '')],
                        ['Crianças:', str(row[35] or '')],
                        ['Adolescentes:', str(row[36] or '')],
                        ['Idosos:', str(row[37] or '')],
                        ['Gestantes:', str(row[38] or '')],
                        ['Nutrizes:', str(row[39] or '')],
                        ['Renda Familiar:', f"R$ {row[40] or '0'}"],
                        ['Renda Per Capita:', f"R$ {row[41] or '0'}"],
                        ['Bolsa Família:', f"R$ {row[42] or '0'}"]
                    ]
                    
                    familia_table = Table(familia_data, colWidths=[120, 350])
                    familia_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    elements.append(familia_table)
                    elements.append(Spacer(1, 15))
                    
                    # Dados Habitacionais
                    casa_para = Paragraph("<b>🏠 Dados Habitacionais</b>", styles['Heading3'])
                    elements.append(casa_para)
                    elements.append(Spacer(1, 6))
                    
                    casa_data = [
                        ['Tipo Casa:', str(row[43] or '')],
                        ['Material Casa:', str(row[44] or '')],
                        ['Energia:', str(row[45] or '')],
                        ['Lixo:', str(row[46] or '')],
                        ['Água:', str(row[47] or '')],
                        ['Esgoto:', str(row[48] or '')]
                    ]
                    
                    casa_table = Table(casa_data, colWidths=[120, 350])
                    casa_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    elements.append(casa_table)
                    elements.append(Spacer(1, 15))
                    
                    # Dados de Saúde
                    saude_para = Paragraph("<b>🏥 Dados de Saúde</b>", styles['Heading3'])
                    elements.append(saude_para)
                    elements.append(Spacer(1, 6))
                    
                    saude_data = [
                        ['Doença Crônica:', str(row[49] or '')],
                        ['Quais Doenças:', str(row[50] or '')],
                        ['Medicamento Contínuo:', str(row[51] or '')],
                        ['Quais Medicamentos:', str(row[52] or '')],
                        ['Doença Mental:', str(row[53] or '')],
                        ['Quais Doenças Mentais:', str(row[54] or '')],
                        ['Deficiência:', str(row[55] or '')],
                        ['Tipo Deficiência:', str(row[56] or '')],
                        ['Cuidados Especiais:', str(row[57] or '')],
                        ['Quais Cuidados:', str(row[58] or '')]
                    ]
                    
                    saude_table = Table(saude_data, colWidths=[120, 350])
                    saude_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    elements.append(saude_table)
                    
                    # Observações
                    if len(row) > 59 and row[59]:
                        elements.append(Spacer(1, 15))
                        obs_para = Paragraph("<b>📝 Observações</b>", styles['Heading3'])
                        elements.append(obs_para)
                        elements.append(Spacer(1, 6))
                        obs_text = Paragraph(str(row[59] or ''), styles['Normal'])
                        elements.append(obs_text)
            else:
                # Tabela resumida para todos os cadastros
                table_data = [['Nome', 'Telefone', 'Bairro', 'Idade', 'Renda']]
                for row in dados:
                    table_data.append([
                        str(row[1] if hasattr(row, '__getitem__') else getattr(row, 'nome_completo', '')),
                        str(row[6] if hasattr(row, '__getitem__') else getattr(row, 'telefone', '')),
                        str(row[4] if hasattr(row, '__getitem__') else getattr(row, 'bairro', '')),
                        str(row[9] if hasattr(row, '__getitem__') else getattr(row, 'idade', '')),
                        f"R$ {row[40] or '0'}" if (hasattr(row, '__getitem__') and row[40]) else 'Não informado'
                    ])
        
        # Criar tabela (exceto para estatístico e cadastro individual que já criaram seus próprios elementos)
        if tipo != 'estatistico' and not cadastro_id:
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(table)
        doc.build(elements)
        
        buffer.seek(0)
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'{filename}.pdf'
        )
    
    # Fallback - não deveria chegar aqui
    flash('Formato de exportação não suportado.')
    return redirect(url_for('relatorios'))

@app.route('/arquivos_saude/<int:cadastro_id>')
def arquivos_saude(cadastro_id):
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    c = cursor = conn[0].cursor() if isinstance(conn, tuple) else conn.cursor()
    
    c.execute('SELECT nome_completo FROM cadastros WHERE id = %s', (cadastro_id,))
    cadastro = c.fetchone()
    
    c.execute('SELECT * FROM arquivos_saude WHERE cadastro_id = %s ORDER BY data_upload DESC', (cadastro_id,))
    arquivos = c.fetchall()
    
    conn.close()
    
    if not cadastro:
        flash('Cadastro não encontrado!')
        return redirect(url_for('relatorio_saude'))
    
    return render_template('arquivos_saude.html', cadastro=cadastro, arquivos=arquivos, cadastro_id=cadastro_id)

@app.route('/download_arquivo/<int:arquivo_id>')
def download_arquivo(arquivo_id):
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    c = cursor = conn[0].cursor() if isinstance(conn, tuple) else conn.cursor()
    c.execute('SELECT nome_arquivo, caminho_arquivo FROM arquivos_saude WHERE id = %s', (arquivo_id,))
    arquivo = c.fetchone()
    conn.close()
    
    if not arquivo or not os.path.exists(arquivo[1]):
        flash('Arquivo não encontrado!')
        return redirect(url_for('relatorio_saude'))
    
    return send_file(arquivo[1], as_attachment=True, download_name=arquivo[0])

@app.route('/upload_arquivo/<int:cadastro_id>', methods=['POST'])
def upload_arquivo(cadastro_id):
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    if 'arquivo' not in request.files:
        flash('Nenhum arquivo selecionado!')
        return redirect(url_for('arquivos_saude', cadastro_id=cadastro_id))
    
    file = request.files['arquivo']
    if file.filename == '':
        flash('Nenhum arquivo selecionado!')
        return redirect(url_for('arquivos_saude', cadastro_id=cadastro_id))
    
    if file and allowed_file(file.filename):
        file_data = file.read()
        
        conn = get_db_connection()
        c = cursor = conn[0].cursor() if isinstance(conn, tuple) else conn.cursor()
        c.execute('INSERT INTO arquivos_saude (cadastro_id, nome_arquivo, tipo_arquivo, arquivo_dados, descricao) VALUES (%s, %s, %s, %s, %s)', 
                (cadastro_id, file.filename, request.form.get('tipo_arquivo'), file_data, request.form.get('descricao')))
        conn.commit()
        conn.close()
        
        flash('Arquivo enviado com sucesso!')
    else:
        flash('Tipo de arquivo não permitido! Use: PDF, PNG, JPG, DOC, DOCX')
    
    return redirect(url_for('arquivos_saude', cadastro_id=cadastro_id))

@app.route('/usuarios')
def usuarios():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    if session['usuario'] != 'admin':
        flash('Acesso negado! Apenas administradores podem gerenciar usuários.')
        return redirect(url_for('dashboard'))
    
    logger.info("📋 Carregando lista de usuários...")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, usuario FROM usuarios ORDER BY usuario')
        usuarios_lista = cursor.fetchall()
        
        logger.debug(f"Encontrados {len(usuarios_lista)} usuários")
        
        cursor.close()
        conn.close()
        
        return render_template('usuarios.html', usuarios=usuarios_lista)
        
    except Exception as e:
        logger.error(f"❌ Erro ao carregar usuários: {e}")
        flash('Erro ao carregar lista de usuários.')
        return render_template('usuarios.html', usuarios=[])

@app.route('/criar_usuario')
def criar_usuario():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    if session['usuario'] != 'admin':
        flash('Acesso negado! Apenas administradores podem criar usuários.')
        return redirect(url_for('dashboard'))
    return render_template('criar_usuario.html')

@app.route('/criar_usuario', methods=['POST'])
def salvar_usuario():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    if session['usuario'] != 'admin':
        flash('Acesso negado! Apenas administradores podem criar usuários.')
        return redirect(url_for('dashboard'))
    
    novo_usuario = request.form['usuario']
    nova_senha = request.form['senha']
    
    logger.info(f"👤 Criando novo usuário: {novo_usuario}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Verificar se usuário já existe
        logger.debug("Verificando se usuário já existe...")
        cursor.execute('SELECT id FROM usuarios WHERE usuario = %s', (novo_usuario,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            logger.warning(f"⚠️ Usuário {novo_usuario} já existe")
            flash(f'Usuário "{novo_usuario}" já existe!')
            cursor.close()
            conn.close()
            return redirect(url_for('usuarios'))
        
        senha_hash = generate_password_hash(nova_senha)
        logger.debug("Hash da senha gerado")
        
        # No Railway sempre será PostgreSQL
        cursor.execute('INSERT INTO usuarios (usuario, senha) VALUES (%s, %s)', (novo_usuario, senha_hash))
        logger.debug("Query INSERT executada")
        
        conn.commit()
        logger.info(f"✅ Usuário {novo_usuario} criado com sucesso!")
        flash('Usuário criado com sucesso!')
    except Exception as e:
        logger.error(f"❌ Erro ao criar usuário {novo_usuario}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        flash(f'Erro ao criar usuário: {str(e)}')
    
    cursor.close()
    conn.close()
    return redirect(url_for('usuarios'))

@app.route('/excluir_usuario/<int:usuario_id>')
def excluir_usuario(usuario_id):
    if 'usuario' not in session:
        return redirect(url_for('login'))
    if session['usuario'] != 'admin':
        flash('Acesso negado! Apenas administradores podem excluir usuários.')
        return redirect(url_for('dashboard'))
    
    logger.info(f"🗑️ Tentando excluir usuário ID: {usuario_id}")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar se é o admin
        cursor.execute('SELECT usuario FROM usuarios WHERE id = %s', (usuario_id,))
        user_data = cursor.fetchone()
        
        if not user_data:
            logger.warning(f"⚠️ Usuário ID {usuario_id} não encontrado")
            flash('Usuário não encontrado!')
            cursor.close()
            conn.close()
            return redirect(url_for('usuarios'))
        
        username = user_data[0] if isinstance(user_data, tuple) else user_data['usuario']
        
        if username == 'admin':
            logger.warning("⚠️ Tentativa de excluir usuário admin bloqueada")
            flash('Não é possível excluir o usuário admin!')
            cursor.close()
            conn.close()
            return redirect(url_for('usuarios'))
        
        # Excluir usuário
        cursor.execute('DELETE FROM usuarios WHERE id = %s', (usuario_id,))
        usuarios_deletados = cursor.rowcount
        
        if usuarios_deletados > 0:
            conn.commit()
            logger.info(f"✅ Usuário {username} (ID: {usuario_id}) excluído com sucesso")
            flash(f'Usuário "{username}" excluído com sucesso!')
        else:
            logger.warning(f"⚠️ Nenhum usuário foi excluído (ID: {usuario_id})")
            flash('Erro: Usuário não foi excluído.')
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ Erro ao excluir usuário ID {usuario_id}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        flash(f'Erro ao excluir usuário: {str(e)}')
    
    return redirect(url_for('usuarios'))

@app.route('/editar_cadastro/<int:cadastro_id>')
def editar_cadastro(cadastro_id):
    if 'usuario' not in session:
        logger.debug("Usuário não logado tentando acessar /editar_cadastro")
        return redirect(url_for('login'))
    
    logger.info(f"📝 Carregando cadastro para edição: ID {cadastro_id}")
    try:
        conn, db_type = get_db()
        cursor = conn.cursor()
        logger.debug(f"Buscando cadastro ID {cadastro_id}")
        
        if db_type == 'postgresql':
            cursor.execute('SELECT * FROM cadastros WHERE id = %s', (cadastro_id,))
        else:
            cursor.execute('SELECT * FROM cadastros WHERE id = ?', (cadastro_id,))
        
        cadastro = cursor.fetchone()
        logger.debug(f"Cadastro encontrado: {cadastro is not None}")
        
        # Buscar arquivos de saúde associados
        arquivos_saude = []
        if cadastro:
            logger.debug("Buscando arquivos de saúde...")
            if db_type == 'postgresql':
                cursor.execute('SELECT id, nome_arquivo, tipo_arquivo, descricao, data_upload FROM arquivos_saude WHERE cadastro_id = %s ORDER BY data_upload DESC', (cadastro_id,))
            else:
                cursor.execute('SELECT id, nome_arquivo, tipo_arquivo, descricao, data_upload FROM arquivos_saude WHERE cadastro_id = ? ORDER BY data_upload DESC', (cadastro_id,))
            
            arquivos_saude = cursor.fetchall()
            logger.debug(f"Encontrados {len(arquivos_saude)} arquivos de saúde")
        
        cursor.close()
        conn.close()
        logger.info("✅ Cadastro e arquivos carregados para edição")
        
        if not cadastro:
            logger.warning(f"⚠️ Cadastro ID {cadastro_id} não encontrado")
            flash('Cadastro não encontrado!')
            return redirect(url_for('dashboard'))
        
        return render_template('editar_cadastro.html', cadastro=cadastro, arquivos_saude=arquivos_saude)
        
    except Exception as e:
        logger.error(f"❌ Erro ao carregar cadastro para edição: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        flash('Erro ao carregar cadastro.')
        return redirect(url_for('dashboard'))

@app.route('/excluir_arquivo/<int:arquivo_id>')
def excluir_arquivo(arquivo_id):
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    try:
        conn, db_type = get_db()
        cursor = conn.cursor()
        
        # Buscar o cadastro_id antes de excluir
        if db_type == 'postgresql':
            cursor.execute('SELECT cadastro_id FROM arquivos_saude WHERE id = %s', (arquivo_id,))
        else:
            cursor.execute('SELECT cadastro_id FROM arquivos_saude WHERE id = ?', (arquivo_id,))
        
        result = cursor.fetchone()
        if not result:
            flash('Arquivo não encontrado!')
            return redirect(url_for('dashboard'))
        
        cadastro_id = result[0] if isinstance(result, tuple) else result['cadastro_id']
        
        # Excluir o arquivo
        if db_type == 'postgresql':
            cursor.execute('DELETE FROM arquivos_saude WHERE id = %s', (arquivo_id,))
        else:
            cursor.execute('DELETE FROM arquivos_saude WHERE id = ?', (arquivo_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Arquivo excluído com sucesso!')
        return redirect(url_for('editar_cadastro', cadastro_id=cadastro_id))
        
    except Exception as e:
        logger.error(f"❌ Erro ao excluir arquivo: {e}")
        flash('Erro ao excluir arquivo.')
        return redirect(url_for('dashboard'))

@app.before_request
def log_request_info():
    if request.endpoint and 'atualizar_cadastro' in request.endpoint:
        logger.info(f"🌐 REQUEST: {request.method} {request.url}")
        logger.info(f"🌐 ENDPOINT: {request.endpoint}")
        logger.info(f"🌐 FORM DATA: {dict(request.form) if request.form else 'None'}")

@app.route('/atualizar_cadastro/<int:cadastro_id>', methods=['POST'])
def atualizar_cadastro(cadastro_id):
    logger.info(f"🔥 ROTA ATUALIZAR_CADASTRO ACESSADA - ID: {cadastro_id}")
    logger.info(f"🔥 METHOD: {request.method}")
    logger.info(f"🔥 URL: {request.url}")
    logger.info(f"🔥 USER-AGENT: {request.headers.get('User-Agent', 'N/A')}")
    
    if 'usuario' not in session:
        logger.debug("Usuário não logado tentando acessar /atualizar_cadastro")
        return redirect(url_for('login'))
    
    logger.info(f"💾 Iniciando atualização do cadastro ID {cadastro_id}")
    logger.debug(f"Dados recebidos: nome_completo={request.form.get('nome_completo')}")
    logger.debug(f"Total de campos no formulário: {len(request.form)}")
    logger.debug(f"Campos recebidos: {list(request.form.keys())[:10]}...")  # Primeiros 10 campos
    
    # Validar limites dos campos
    logger.debug("Iniciando validação de limites dos campos...")
    validation_errors = validate_field_lengths(request.form)
    if validation_errors:
        logger.error(f"❌ Validação falhou: {len(validation_errors)} erros encontrados")
        logger.error(f"Erros: {validation_errors}")
        for error in validation_errors:
            flash(f"Erro de validação: {error}", 'error')
        return redirect(url_for('editar_cadastro', cadastro_id=cadastro_id))
    
    logger.debug("✅ Validação de limites passou")
    
    try:
        logger.debug("Obtendo conexão com banco de dados...")
        conn, db_type = get_db()
        cursor = conn.cursor()
        logger.debug(f"Conexão estabelecida - Tipo: {db_type}")
        
        # Campos do formulário
        campos = [
            'nome_completo', 'endereco', 'numero', 'bairro', 'cep', 'cidade', 'estado', 'telefone', 'ponto_referencia',
            'genero', 'idade', 'data_nascimento', 'titulo_eleitor', 'cidade_titulo',
            'cpf', 'rg', 'nis', 'estado_civil', 'escolaridade', 'profissao',
            'nome_companheiro', 'cpf_companheiro', 'rg_companheiro', 'idade_companheiro',
            'escolaridade_companheiro', 'profissao_companheiro', 'data_nascimento_companheiro',
            'titulo_companheiro', 'cidade_titulo_companheiro', 'nis_companheiro', 'tipo_trabalho',
            'pessoas_trabalham', 'aposentados_pensionistas', 'num_pessoas_familia', 'num_familias',
            'adultos', 'criancas', 'adolescentes', 'idosos', 'gestantes', 'nutrizes',
            'renda_familiar', 'renda_per_capita', 'bolsa_familia', 'casa_tipo', 'casa_material',
            'energia', 'lixo', 'agua', 'esgoto', 'observacoes', 'tem_doenca_cronica',
            'doencas_cronicas', 'usa_medicamento_continuo', 'medicamentos_continuos',
            'tem_doenca_mental', 'doencas_mentais', 'tem_deficiencia', 'tipo_deficiencia',
            'precisa_cuidados_especiais', 'cuidados_especiais',
            # Novos campos de trabalho
            'com_que_trabalha', 'onde_trabalha', 'localizacao_trabalho', 'horario_trabalho', 'tempo_atividade',
            'atua_ponto_fixo', 'qual_ponto_fixo', 'dias_semana_trabalha', 'trabalho_continuo_temporada',
            'sofreu_acidente_trabalho', 'qual_acidente', 'trabalho_incomoda_calor',
            'trabalho_incomoda_barulho', 'trabalho_incomoda_seguranca', 'trabalho_incomoda_banheiros',
            'trabalho_incomoda_outro', 'trabalho_incomoda_outro_desc', 'acesso_banheiro_agua',
            'trabalha_sozinho_ajudantes', 'possui_autorizacao_municipal', 'problemas_fiscalizacao_policia',
            'estrutura_barraca', 'estrutura_carrinho', 'estrutura_mesa', 'estrutura_outro',
            'estrutura_outro_desc', 'necessita_energia_eletrica', 'utiliza_gas_cozinha',
            'usa_veiculo_proprio', 'qual_veiculo', 'fonte_renda_trabalho_ambulante',
            'fonte_renda_aposentadoria', 'fonte_renda_outro_trabalho', 'fonte_renda_beneficio_social',
            'fonte_renda_outro', 'fonte_renda_outro_desc', 'pessoas_dependem_renda'
        ]
        
        logger.debug(f"Total de campos para atualização: {len(campos)}")
        
        # Tratar campos numéricos vazios como NULL
        def safe_int_or_null(value):
            if value == '' or value is None:
                return None
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
        
        def safe_decimal_or_null(value):
            if value == '' or value is None:
                return None
            try:
                return float(value)
            except (ValueError, TypeError):
                return None
        
        # Campos que devem ser tratados como inteiros
        campos_int = ['idade', 'idade_companheiro', 'pessoas_trabalham', 'aposentados_pensionistas', 
                     'num_pessoas_familia', 'num_familias', 'adultos', 'criancas', 'adolescentes', 
                     'idosos', 'gestantes', 'nutrizes', 'dias_semana_trabalha', 'pessoas_dependem_renda']
        
        # Campos que devem ser tratados como decimais
        campos_decimal = ['renda_familiar', 'renda_per_capita', 'bolsa_familia']
        
        valores = []
        for campo in campos:
            value = request.form.get(campo, '')
            if campo in campos_int:
                valores.append(safe_int_or_null(value))
            elif campo in campos_decimal:
                valores.append(safe_decimal_or_null(value))
            else:
                valores.append(value)
        
        valores.append(cadastro_id)
        
        logger.debug(f"Valores coletados: {len(valores)} valores")
        logger.debug(f"Primeiros 5 valores: {valores[:5]}")
        logger.debug(f"Últimos 5 valores: {valores[-5:]}")
        
        # Construir query UPDATE dinamicamente baseada na lista de campos
        placeholder = '%s' if db_type == 'postgresql' else '?'
        set_clauses = [f"{campo} = {placeholder}" for campo in campos]
        sql_update = f"""
        UPDATE cadastros SET 
        {', '.join(set_clauses)}
        WHERE id = {placeholder}
        """
        
        logger.debug(f"Query UPDATE construída com {len(set_clauses)} campos")
        logger.debug(f"Query: {sql_update[:200]}...")
        
        logger.debug("Executando query UPDATE...")
        cursor.execute(sql_update, valores)
        
        rows_affected = cursor.rowcount
        logger.debug(f"Linhas afetadas: {rows_affected}")
        
        if rows_affected > 0:
            conn.commit()
            logger.info(f"✅ Cadastro {cadastro_id} atualizado com sucesso")
            flash('Cadastro atualizado com sucesso!')
        else:
            logger.warning(f"⚠️ Nenhuma linha foi atualizada para cadastro {cadastro_id}")
            flash('Nenhuma alteração foi feita no cadastro.')
        
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar cadastro {cadastro_id}: {str(e)}")
        logger.error(f"Tipo do erro: {type(e)}")
        import traceback
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        # Não mostrar erro técnico para o usuário
        flash('Erro interno do sistema. Tente novamente.')
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        logger.debug("Conexões fechadas")
        logger.debug("Conexão fechada após atualização")
    
    return redirect(url_for('dashboard'))

@app.route('/deletar_cadastro/<int:cadastro_id>', methods=['POST'])
def deletar_cadastro(cadastro_id):
    if 'usuario' not in session:
        logger.debug("Usuário não logado tentando acessar /deletar_cadastro")
        return redirect(url_for('login'))
    
    logger.info(f"🗑️ Tentando deletar cadastro ID: {cadastro_id}")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        logger.debug("Conexão estabelecida para deleção")
        
        # Deletar arquivos de saúde relacionados primeiro
        logger.debug("Deletando arquivos de saúde relacionados...")
        cursor.execute('DELETE FROM arquivos_saude WHERE cadastro_id = %s', (cadastro_id,))
        arquivos_deletados = cursor.rowcount
        logger.debug(f"Arquivos deletados: {arquivos_deletados}")
        
        # Deletar o cadastro
        logger.debug("Deletando cadastro principal...")
        cursor.execute('DELETE FROM cadastros WHERE id = %s', (cadastro_id,))
        cadastros_deletados = cursor.rowcount
        
        if cadastros_deletados > 0:
            conn.commit()
            logger.info(f"✅ Cadastro {cadastro_id} deletado com sucesso")
            flash('Cadastro deletado com sucesso!')
        else:
            logger.warning(f"⚠️ Cadastro {cadastro_id} não encontrado para deleção")
            flash('Cadastro não encontrado!')
            
    except Exception as e:
        logger.error(f"❌ Erro ao deletar cadastro {cadastro_id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        flash(f'Erro ao deletar cadastro: {str(e)}')
    finally:
        cursor.close()
        conn.close()
        logger.debug("Conexão fechada após deleção")
    
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🚀 Iniciando AMEG na porta {port}")
    logger.info(f"Debug mode: {app.debug}")
    logger.info(f"Environment: {'Railway' if os.environ.get('RAILWAY_ENVIRONMENT') else 'Local'}")
    app.run(host='0.0.0.0', port=port, debug=False)
