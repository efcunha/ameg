from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, send_from_directory
from flask_compress import Compress
from database import get_db_connection, init_db_tables, create_admin_user, registrar_auditoria, inserir_movimentacao_caixa, inserir_comprovante_caixa, listar_movimentacoes_caixa, obter_saldo_caixa, listar_cadastros_simples, usuario_tem_permissao, adicionar_permissao_usuario, obter_permissoes_usuario, remover_permissao_usuario, obter_comprovantes_movimentacao
import psycopg2.extras
import os
import gzip

# Cache simples em memória para estatísticas
stats_cache = {
    'data': None,
    'timestamp': None,
    'ttl': 300  # 5 minutos
}

def get_cached_stats():
    """Retorna estatísticas do cache ou busca no banco se expirado"""
    now = datetime.now()
    
    # Verificar se cache é válido
    if (stats_cache['data'] is not None and 
        stats_cache['timestamp'] is not None and
        (now - stats_cache['timestamp']).seconds < stats_cache['ttl']):
        return stats_cache['data']
    
    # Cache expirado, buscar dados atualizados
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Contar registros otimizado
        cursor.execute('SELECT COUNT(*) FROM cadastros')
        total_cadastros = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM arquivos_saude')
        total_arquivos = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM usuarios WHERE tipo = %s', ('admin',))
        total_admins = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        # Atualizar cache
        stats_cache['data'] = {
            'total': total_cadastros,
            'arquivos': total_arquivos,
            'admins': total_admins
        }
        stats_cache['timestamp'] = now
        
        return stats_cache['data']
        
    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas: {e}")
        return {'total': 0, 'arquivos': 0, 'admins': 0}

def invalidate_stats_cache():
    """Invalida o cache de estatísticas"""
    stats_cache['data'] = None
    stats_cache['timestamp'] = None
from psycopg2.extras import RealDictCursor
import csv
import io
import os
import logging
import traceback
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Configurar logging detalhado
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'ameg_secret_2024_fallback_key_change_in_production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Configurar compressão
Compress(app)

# Middleware para servir arquivos comprimidos
@app.after_request
def after_request(response):
    # Adiciona headers de cache para arquivos estáticos
    if request.endpoint == 'static':
        response.cache_control.max_age = 31536000  # 1 ano
        response.cache_control.public = True
    
    # Compressão manual para arquivos CSS/JS se disponível
    if (request.endpoint == 'static' and 
        'gzip' in request.accept_encodings and
        (request.path.endswith('.css') or request.path.endswith('.js'))):
        
        gzip_path = request.path + '.gz'
        if os.path.exists('static' + gzip_path.replace('/static', '')):
            response.headers['Content-Encoding'] = 'gzip'
    
    return response

logger.info("🚀 Iniciando aplicação AMEG")
logger.info(f"RAILWAY_ENVIRONMENT: {os.environ.get('RAILWAY_ENVIRONMENT')}")

# Função helper para verificar se usuário é admin
def is_admin_user(username):
    """Verifica se o usuário tem privilégios de administrador"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT tipo FROM usuarios WHERE usuario = %s', (username,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            tipo = result[0] if isinstance(result, tuple) else result.get('tipo', 'usuario')
            return tipo == 'admin'
        return username == 'admin'  # Fallback para compatibilidade
    except Exception as e:
        logger.error(f"Erro ao verificar admin: {e}")
        return username == 'admin'  # Fallback para compatibilidade

# Disponibilizar função para templates
@app.context_processor
def inject_user_functions():
    return dict(is_admin_user=is_admin_user)
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
    logger.info("🏠 Ambiente local detectado - usando PostgreSQL")

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

@app.route('/logo')
def logo():
    """Rota específica para o logo"""
    return send_from_directory('static/img', 'logo-ameg.jpeg')

@app.route('/')
def login():
    if 'usuario' in session:
        return redirect(url_for('dashboard'))
    
    # Limpar mensagens flash antigas na tela de login
    session.pop('_flashes', None)
    
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def fazer_login():
    usuario = request.form['usuario']
    senha = request.form['senha']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # No Railway sempre será PostgreSQL
    cursor.execute('SELECT senha, tipo FROM usuarios WHERE usuario = %s', (usuario,))
    
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if user and check_password_hash(user[0], senha):
        session['usuario'] = usuario
        session['tipo'] = user[1]  # Definir o tipo na sessão
        
        # Registrar auditoria de login
        registrar_auditoria(
            usuario=usuario,
            acao='LOGIN',
            tabela='usuarios',
            dados_novos=f"Login realizado com sucesso",
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
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
    
    # Usar cache para estatísticas
    stats = get_cached_stats()
    
    # Verificar permissão de caixa
    tem_permissao_caixa = usuario_tem_permissao(session['usuario'], 'caixa')
    
    # Buscar últimos cadastros (não cachear pois muda frequentemente)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, nome_completo, telefone, bairro, data_cadastro FROM cadastros ORDER BY data_cadastro DESC LIMIT 5')
    ultimos = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('dashboard.html', 
                         total=stats['total'], 
                         ultimos=ultimos,
                         tem_permissao_caixa=tem_permissao_caixa)

@app.route('/arquivos_cadastros')
def arquivos_cadastros():
    import logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    
    logger.info("=== INICIANDO arquivos_cadastros ===")
    
    if 'usuario' not in session:
        logger.warning("Usuário não autenticado, redirecionando para login")
        return redirect(url_for('login'))
    
    logger.info(f"Usuário autenticado: {session.get('usuario')}")
    
    try:
        logger.info("Tentando conectar ao banco de dados")
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        logger.info("Conexão com banco estabelecida com sucesso")
        
        # Buscar apenas cadastros que têm arquivos anexados
        query_cadastros = '''
            SELECT c.id, c.nome_completo, c.cpf,
                   COUNT(a.id) as arquivos_count
            FROM cadastros c
            INNER JOIN arquivos_saude a ON c.id = a.cadastro_id
            GROUP BY c.id, c.nome_completo, c.cpf
            HAVING COUNT(a.id) > 0
            ORDER BY c.nome_completo
        '''
        logger.info(f"Executando query principal: {query_cadastros}")
        cursor.execute(query_cadastros)
        cadastros_data = cursor.fetchall()
        logger.info(f"Query executada com sucesso. {len(cadastros_data)} cadastros encontrados")
        
        cadastros = []
        for i, cadastro_data in enumerate(cadastros_data):
            logger.info(f"Processando cadastro {i+1}/{len(cadastros_data)}: ID={cadastro_data['id']}, Nome={cadastro_data['nome_completo']}")
            
            # Buscar arquivos de saúde para cada cadastro
            query_arquivos = '''
                SELECT id, tipo_arquivo, nome_arquivo, descricao, data_upload
                FROM arquivos_saude 
                WHERE cadastro_id = %s
                ORDER BY data_upload DESC
            '''
            logger.info(f"Buscando arquivos para cadastro ID {cadastro_data['id']}")
            cursor.execute(query_arquivos, (cadastro_data['id'],))
            arquivos = cursor.fetchall()
            logger.info(f"Encontrados {len(arquivos)} arquivos para cadastro ID {cadastro_data['id']}")
            
            cadastro_obj = {
                'id': cadastro_data['id'],
                'nome_completo': cadastro_data['nome_completo'],
                'cpf': cadastro_data['cpf'],
                'arquivos_count': cadastro_data['arquivos_count'],
                'arquivos_saude': arquivos
            }
            cadastros.append(cadastro_obj)
            logger.debug(f"Cadastro processado: {cadastro_obj}")
        
        cursor.close()
        conn.close()
        logger.info("Conexão com banco fechada")
        
        logger.info(f"Renderizando template com {len(cadastros)} cadastros")
        return render_template('arquivos_cadastros.html', cadastros=cadastros)
        
    except Exception as e:
        logger.error(f"ERRO em arquivos_cadastros: {str(e)}")
        logger.error(f"Tipo do erro: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        
        try:
            cursor.close()
            conn.close()
            logger.info("Conexão fechada após erro")
        except:
            logger.error("Erro ao fechar conexão")
        
        flash(f'Erro ao carregar arquivos: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/exportar_arquivos_pdf/<int:cadastro_id>')
def exportar_arquivos_pdf(cadastro_id):
    import logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    
    logger.info(f"=== INICIANDO exportar_arquivos_pdf para cadastro_id={cadastro_id} ===")
    
    if 'usuario' not in session:
        logger.warning("Usuário não autenticado, redirecionando para login")
        return redirect(url_for('login'))
    
    logger.info(f"Usuário autenticado: {session.get('usuario')}")
    
    try:
        logger.info("Conectando ao banco de dados")
        conn = get_db_connection()
        cursor = conn.cursor()
        logger.info("Conexão estabelecida")
        
        # Buscar dados do cadastro
        query_cadastro = 'SELECT * FROM cadastros WHERE id = %s'
        logger.info(f"Buscando cadastro: {query_cadastro} com ID={cadastro_id}")
        cursor.execute(query_cadastro, (cadastro_id,))
        cadastro = cursor.fetchone()
        
        if not cadastro:
            logger.warning(f"Cadastro ID {cadastro_id} não encontrado")
            cursor.close()
            conn.close()
            return "Cadastro não encontrado", 404
        
        logger.info(f"Cadastro encontrado: {cadastro[1]} (ID: {cadastro[0]})")
        
        # Buscar arquivos de saúde
        query_arquivos = '''
            SELECT tipo_arquivo, nome_arquivo, descricao, data_upload, caminho_arquivo
            FROM arquivos_saude 
            WHERE cadastro_id = %s
            ORDER BY tipo_arquivo, data_upload
        '''
        logger.info(f"Buscando arquivos: {query_arquivos}")
        cursor.execute(query_arquivos, (cadastro_id,))
        arquivos = cursor.fetchall()
        logger.info(f"Encontrados {len(arquivos)} arquivos")
        
        for i, arquivo in enumerate(arquivos):
            logger.debug(f"Arquivo {i+1}: tipo={arquivo[0]}, nome={arquivo[1]}, desc={arquivo[2]}")
        
        cursor.close()
        conn.close()
        logger.info("Conexão fechada")
        
        # Gerar PDF
        logger.info("Iniciando geração do PDF")
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from io import BytesIO
        
        logger.info("Imports do ReportLab realizados com sucesso")
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch)
        styles = getSampleStyleSheet()
        story = []
        logger.info("Documento PDF inicializado")
        
        # Título
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, spaceAfter=20)
        story.append(Paragraph(f"Relatório de Arquivos de Saúde", title_style))
        logger.info("Título adicionado")
        
        # Dados do cadastro
        nome = cadastro[1] or 'N/A'
        cpf = cadastro[13] or 'N/A'
        telefone = cadastro[6] or 'N/A'
        
        story.append(Paragraph(f"<b>Nome:</b> {nome}", styles['Normal']))
        story.append(Paragraph(f"<b>CPF:</b> {cpf}", styles['Normal']))
        story.append(Paragraph(f"<b>Telefone:</b> {telefone}", styles['Normal']))
        story.append(Spacer(1, 20))
        logger.info("Dados do cadastro adicionados")
        
        # Lista de arquivos
        if arquivos:
            logger.info("Processando lista de arquivos")
            story.append(Paragraph("<b>Arquivos de Saúde Anexados:</b>", styles['Heading2']))
            story.append(Spacer(1, 10))
            
            # Agrupar por tipo
            tipos = {}
            for arquivo in arquivos:
                tipo = arquivo[0]
                if tipo not in tipos:
                    tipos[tipo] = []
                tipos[tipo].append(arquivo)
            
            logger.info(f"Arquivos agrupados em {len(tipos)} tipos: {list(tipos.keys())}")
            
            for tipo, lista_arquivos in tipos.items():
                logger.info(f"Processando tipo '{tipo}' com {len(lista_arquivos)} arquivos")
                story.append(Paragraph(f"<b>{tipo.title()}:</b>", styles['Heading3']))
                
                for arquivo in lista_arquivos:
                    story.append(Paragraph(f"• {arquivo[1]}", styles['Normal']))
                    if arquivo[2]:  # descrição
                        story.append(Paragraph(f"  <i>{arquivo[2]}</i>", styles['Normal']))
                    story.append(Paragraph(f"  Data: {arquivo[3].strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
                    story.append(Spacer(1, 5))
                
                story.append(Spacer(1, 10))
        else:
            logger.info("Nenhum arquivo encontrado")
            story.append(Paragraph("Nenhum arquivo de saúde anexado.", styles['Normal']))
        
        logger.info("Construindo documento PDF")
        doc.build(story)
        buffer.seek(0)
        logger.info("PDF gerado com sucesso")
        
        filename = f'arquivos_saude_{nome.replace(" ", "_")}.pdf'
        logger.info(f"Enviando arquivo: {filename}")
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"ERRO CRÍTICO em exportar_arquivos_pdf: {str(e)}")
        logger.error(f"Tipo do erro: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        
        try:
            cursor.close()
            conn.close()
            logger.info("Conexão fechada após erro")
        except:
            logger.error("Erro ao fechar conexão após erro principal")
        
        flash(f'Erro ao gerar PDF: {str(e)}', 'error')
        return redirect(url_for('arquivos_cadastros'))

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
            conn = get_db_connection()
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
                safe_int_or_null(request.form.get('pessoas_dependem_renda')),
                request.form.get('foto_base64')  # Campo da foto
            )
            
            logger.debug(f"📊 Preparando INSERT com {len(dados_insert)} valores")
            logger.debug(f"🔍 Primeiros 5 valores: {dados_insert[:5]}")
            logger.debug(f"🔍 Últimos 5 valores: {dados_insert[-5:]}")
            
            logger.debug("Executando INSERT para novo cadastro...")
            cursor.execute("""INSERT INTO cadastros (
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
            fonte_renda_outro_desc, pessoas_dependem_renda, foto_base64
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            dados_insert)
            conn.commit()
            
            logger.info("✅ INSERT executado com sucesso!")
            
            # Invalidar cache de estatísticas
            invalidate_stats_cache()
            
            # Registrar auditoria
            registrar_auditoria(
                usuario=session.get('usuario', 'Sistema'),
                acao='INSERT',
                tabela='cadastros',
                dados_novos=f"Nome: {request.form.get('nome_completo')}, CPF: {request.form.get('cpf')}",
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
        
            # Para obter o ID do cadastro inserido, usar a mesma conexão
            logger.debug("🔍 Buscando ID do cadastro inserido...")
            
            cursor.execute('SELECT id FROM cadastros ORDER BY id DESC LIMIT 1')
            
            result = cursor.fetchone()
            if result:
                # PostgreSQL RealDictCursor
                if hasattr(result, 'keys'):
                    cadastro_id = result['id']
                else:  # Tuple result
                    cadastro_id = result[0]
                logger.debug(f"ID do cadastro inserido: {cadastro_id}")
            else:
                cadastro_id = None
                logger.error("❌ Não foi possível obter o ID do cadastro inserido")
            
            # Upload de arquivos usando a mesma conexão
            uploaded_files = []
            if cadastro_id:
                for file_type in ['laudo', 'receita', 'imagem']:
                    # Processar arrays de arquivos
                    files = request.files.getlist(f'{file_type}[]')
                    descriptions = request.form.getlist(f'descricao_{file_type}[]')
                    
                    for i, file in enumerate(files):
                        if file and file.filename and allowed_file(file.filename):
                            logger.debug(f"Processando arquivo: {file.filename} ({file_type})")
                            file_data = file.read()
                            descricao = descriptions[i] if i < len(descriptions) else ''
                            
                            cursor.execute('INSERT INTO arquivos_saude (cadastro_id, nome_arquivo, tipo_arquivo, arquivo_dados, descricao) VALUES (%s, %s, %s, %s, %s)', 
                                        (cadastro_id, file.filename, file_type, file_data, descricao))
                            
                            uploaded_files.append(f"{file_type}: {file.filename}")
                            logger.debug(f"Arquivo {file.filename} salvo com sucesso")
            
            # Processar dados de saúde por pessoa
            if cadastro_id:
                logger.debug("Processando dados de saúde por pessoa...")
                pessoas_saude = []
                
                # Buscar todos os campos de saúde por pessoa
                for key in request.form.keys():
                    if key.startswith('saude_nome_'):
                        pessoa_num = key.split('_')[-1]
                        nome_pessoa = request.form.get(f'saude_nome_{pessoa_num}')
                        
                        if nome_pessoa:  # Só processar se tem nome
                            # Processar checkboxes de condições
                            condicoes = request.form.getlist(f'saude_condicoes_{pessoa_num}[]')
                            
                            dados_pessoa = {
                                'nome_pessoa': nome_pessoa,
                                'tem_doenca_cronica': 'Sim' if 'doenca_cronica' in condicoes else 'Não',
                                'doencas_cronicas': request.form.get(f'saude_doencas_cronicas_{pessoa_num}', ''),
                                'usa_medicamento_continuo': 'Sim' if 'medicamento' in condicoes else 'Não',
                                'medicamentos': request.form.get(f'saude_medicamentos_{pessoa_num}', ''),
                                'tem_doenca_mental': 'Sim' if 'doenca_mental' in condicoes else 'Não',
                                'doencas_mentais': request.form.get(f'saude_doencas_mentais_{pessoa_num}', ''),
                                'tem_deficiencia': 'Sim' if 'deficiencia' in condicoes else 'Não',
                                'deficiencias': request.form.get(f'saude_deficiencias_{pessoa_num}', ''),
                                'precisa_cuidados_especiais': 'Sim' if 'cuidados' in condicoes else 'Não',
                                'cuidados_especiais': request.form.get(f'saude_cuidados_especiais_{pessoa_num}', '')
                            }
                            
                            # Inserir dados de saúde da pessoa
                            cursor.execute('''
                                INSERT INTO dados_saude_pessoa (
                                    cadastro_id, nome_pessoa, tem_doenca_cronica, doencas_cronicas,
                                    usa_medicamento_continuo, medicamentos, tem_doenca_mental, doencas_mentais,
                                    tem_deficiencia, deficiencias, precisa_cuidados_especiais, cuidados_especiais
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ''', (
                                cadastro_id, dados_pessoa['nome_pessoa'], dados_pessoa['tem_doenca_cronica'],
                                dados_pessoa['doencas_cronicas'], dados_pessoa['usa_medicamento_continuo'],
                                dados_pessoa['medicamentos'], dados_pessoa['tem_doenca_mental'],
                                dados_pessoa['doencas_mentais'], dados_pessoa['tem_deficiencia'],
                                dados_pessoa['deficiencias'], dados_pessoa['precisa_cuidados_especiais'],
                                dados_pessoa['cuidados_especiais']
                            ))
                            
                            pessoas_saude.append(nome_pessoa)
                            logger.debug(f"Dados de saúde salvos para: {nome_pessoa}")
                
                logger.info(f"✅ Dados de saúde salvos para {len(pessoas_saude)} pessoas")
            
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
    
    # Paginação
    page = int(request.args.get('page', 1))
    per_page = 50  # 50 registros por página
    offset = (page - 1) * per_page
    
    try:
        logger.info("📊 Obtendo conexão com banco de dados...")
        conn = get_db_connection()
        cursor = conn.cursor()
        logger.info("✅ Conexão estabelecida")
        
        # Contar total de registros
        cursor.execute('SELECT COUNT(*) FROM cadastros')
        total_records = cursor.fetchone()[0]
        total_pages = (total_records + per_page - 1) // per_page
        
        logger.info(f"🔍 Executando query paginada (página {page}/{total_pages})...")
        cursor.execute('SELECT * FROM cadastros ORDER BY nome_completo LIMIT %s OFFSET %s', (per_page, offset))
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
        return render_template('relatorio_completo.html', 
                             cadastros=cadastros,
                             page=page,
                             total_pages=total_pages,
                             total_records=total_records)
        
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
        
        # Query mais simples primeiro para testar
        cursor.execute('SELECT COUNT(*) FROM cadastros')
        total_cadastros = cursor.fetchone()[0]
        logger.info(f"📊 Total de cadastros na base: {total_cadastros}")
        
        if total_cadastros == 0:
            logger.warning("⚠️ Nenhum cadastro encontrado na base de dados")
            cursor.close()
            conn.close()
            return render_template('relatorio_por_bairro.html', bairros=[], erro="Nenhum cadastro encontrado")
        
        # Query principal - simplificada para testar
        query = '''SELECT bairro, COUNT(*) as total, 
                   AVG(renda_familiar) as renda_media
                   FROM cadastros 
                   WHERE bairro IS NOT NULL AND bairro != ''
                   GROUP BY bairro 
                   ORDER BY total DESC'''
        logger.info(f"🔍 Executando query: {query}")
        cursor.execute(query)
        
        bairros = cursor.fetchall()
        logger.info(f"✅ Bairros encontrados: {len(bairros)}")
        
        if bairros:
            logger.info(f"🔍 Primeiro bairro: {bairros[0]}")
        else:
            logger.warning("⚠️ Nenhum bairro encontrado com dados válidos")
        
        cursor.close()
        conn.close()
        
        return render_template('relatorio_por_bairro.html', bairros=bairros)
        
    except Exception as e:
        logger.error(f"❌ ERRO em relatorio_por_bairro: {str(e)}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return render_template('relatorio_por_bairro.html', bairros=[], erro=f"Erro: {str(e)}")
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
        
        # Faixas de renda - simplificado
        query1 = '''SELECT 
            CASE 
                WHEN renda_familiar IS NOT NULL AND renda_familiar <= 1000 THEN 'Até R$ 1.000'
                WHEN renda_familiar IS NOT NULL AND renda_familiar BETWEEN 1001 AND 2000 THEN 'R$ 1.001 - R$ 2.000'
                WHEN renda_familiar IS NOT NULL AND renda_familiar BETWEEN 2001 AND 3000 THEN 'R$ 2.001 - R$ 3.000'
                WHEN renda_familiar IS NOT NULL AND renda_familiar > 3000 THEN 'Acima de R$ 3.000'
                ELSE 'Não informado'
            END as faixa_renda,
            COUNT(*) 
            FROM cadastros 
            GROUP BY faixa_renda'''
        logger.info(f"🔍 Executando query faixas de renda: {query1}")
        cursor.execute(query1)
        faixas_renda = cursor.fetchall()
        logger.info(f"✅ Faixas de renda encontradas: {len(faixas_renda)}")
        
        # Renda por bairro - simplificado
        query2 = '''SELECT bairro, 
                     AVG(renda_familiar) as renda_media, 
                     COUNT(*) as total
                     FROM cadastros 
                     WHERE bairro IS NOT NULL AND bairro != ''
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
    
    # Parâmetros de filtro
    busca_nome = request.args.get('busca_nome', '').strip()
    ordem = request.args.get('ordem', 'asc')
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Estatísticas usando a nova tabela dados_saude_pessoa
    cursor.execute('SELECT COUNT(DISTINCT cadastro_id) FROM dados_saude_pessoa WHERE tem_doenca_cronica = %s', ('Sim',))
    com_doenca_cronica = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(DISTINCT cadastro_id) FROM dados_saude_pessoa WHERE usa_medicamento_continuo = %s', ('Sim',))
    usa_medicamento = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(DISTINCT cadastro_id) FROM dados_saude_pessoa WHERE tem_doenca_mental = %s', ('Sim',))
    com_doenca_mental = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(DISTINCT cadastro_id) FROM dados_saude_pessoa WHERE tem_deficiencia = %s', ('Sim',))
    com_deficiencia = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(DISTINCT cadastro_id) FROM dados_saude_pessoa WHERE precisa_cuidados_especiais = %s', ('Sim',))
    precisa_cuidados = cursor.fetchone()['count']
    
    # Query principal - buscar cadastros com dados de saúde e suas pessoas
    base_query = """SELECT DISTINCT c.id, c.nome_completo, c.idade, c.telefone, c.bairro
                FROM cadastros c
                INNER JOIN dados_saude_pessoa dsp ON c.id = dsp.cadastro_id
                WHERE (dsp.tem_doenca_cronica = %s OR dsp.usa_medicamento_continuo = %s 
                OR dsp.tem_doenca_mental = %s OR dsp.tem_deficiencia = %s 
                OR dsp.precisa_cuidados_especiais = %s)"""
    
    params = ['Sim', 'Sim', 'Sim', 'Sim', 'Sim']
    
    # Adicionar filtro por nome se fornecido
    if busca_nome:
        base_query += " AND LOWER(c.nome_completo) LIKE LOWER(%s)"
        params.append(f'%{busca_nome}%')
    
    # Adicionar ordenação
    if ordem == 'desc':
        base_query += " ORDER BY c.nome_completo DESC"
    else:
        base_query += " ORDER BY c.nome_completo ASC"
    
    cursor.execute(base_query, params)
    cadastros_base = cursor.fetchall()
    
    # Para cada cadastro, buscar os dados detalhados de saúde de cada pessoa
    cadastros_saude = []
    for cadastro in cadastros_base:
        cursor.execute("""SELECT nome_pessoa, tem_doenca_cronica, doencas_cronicas,
                         usa_medicamento_continuo, medicamentos, tem_doenca_mental, doencas_mentais,
                         tem_deficiencia, deficiencias, precisa_cuidados_especiais, cuidados_especiais
                         FROM dados_saude_pessoa 
                         WHERE cadastro_id = %s 
                         AND (tem_doenca_cronica = 'Sim' OR usa_medicamento_continuo = 'Sim' 
                         OR tem_doenca_mental = 'Sim' OR tem_deficiencia = 'Sim' 
                         OR precisa_cuidados_especiais = 'Sim')
                         ORDER BY nome_pessoa""", (cadastro['id'],))
        pessoas_saude = cursor.fetchall()
        
        if pessoas_saude:  # Só adicionar se tem pessoas com condições de saúde
            cadastros_saude.append({
                'cadastro': cadastro,
                'pessoas_saude': pessoas_saude
            })
    
    cursor.close()
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
    logger.info("🚀 FUNÇÃO EXPORTAR CHAMADA")
    logger.info(f"🔍 Args recebidos: {dict(request.args)}")
    
    if 'usuario' not in session:
        logger.warning("❌ Usuário não logado")
        return redirect(url_for('login'))
    
    tipo = request.args.get('tipo', 'completo')
    formato = request.args.get('formato', 'csv')
    cadastro_id = request.args.get('cadastro_id')  # Para exportar cadastro individual
    
    logger.info(f"🔄 Exportando: tipo={tipo}, formato={formato}, cadastro_id={cadastro_id}")
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
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
        if cadastro_id:
            logger.info(f"🏥 Buscando dados de saúde para cadastro_id={cadastro_id}")
            # Buscar cadastro específico
            cursor.execute('SELECT id, nome_completo, idade, telefone, bairro FROM cadastros WHERE id = %s', (cadastro_id,))
            cadastro_base = cursor.fetchone()
            
            if cadastro_base:
                # Buscar dados de saúde das pessoas
                cursor.execute("""SELECT nome_pessoa, tem_doenca_cronica, doencas_cronicas,
                                 usa_medicamento_continuo, medicamentos, tem_doenca_mental, doencas_mentais,
                                 tem_deficiencia, deficiencias, precisa_cuidados_especiais, cuidados_especiais
                                 FROM dados_saude_pessoa 
                                 WHERE cadastro_id = %s 
                                 AND (tem_doenca_cronica = 'Sim' OR usa_medicamento_continuo = 'Sim' 
                                 OR tem_doenca_mental = 'Sim' OR tem_deficiencia = 'Sim' 
                                 OR precisa_cuidados_especiais = 'Sim')
                                 ORDER BY nome_pessoa""", (cadastro_id,))
                pessoas_saude = cursor.fetchall()
                dados = [{'cadastro': cadastro_base, 'pessoas_saude': pessoas_saude}]
            else:
                dados = []
            filename = f'relatorio_saude_{cadastro_id}'
        else:
            logger.info("🏥 Buscando todos os dados de saúde")
            # Buscar todos os cadastros com dados de saúde
            cursor.execute("""SELECT DISTINCT c.id, c.nome_completo, c.idade, c.telefone, c.bairro
                            FROM cadastros c
                            INNER JOIN dados_saude_pessoa dsp ON c.id = dsp.cadastro_id
                            WHERE (dsp.tem_doenca_cronica = 'Sim' OR dsp.usa_medicamento_continuo = 'Sim' 
                            OR dsp.tem_doenca_mental = 'Sim' OR dsp.tem_deficiencia = 'Sim' 
                            OR dsp.precisa_cuidados_especiais = 'Sim')
                            ORDER BY c.nome_completo""")
            cadastros_base = cursor.fetchall()
            
            dados = []
            for cadastro in cadastros_base:
                cursor.execute("""SELECT nome_pessoa, tem_doenca_cronica, doencas_cronicas,
                                 usa_medicamento_continuo, medicamentos, tem_doenca_mental, doencas_mentais,
                                 tem_deficiencia, deficiencias, precisa_cuidados_especiais, cuidados_especiais
                                 FROM dados_saude_pessoa 
                                 WHERE cadastro_id = %s 
                                 AND (tem_doenca_cronica = 'Sim' OR usa_medicamento_continuo = 'Sim' 
                                 OR tem_doenca_mental = 'Sim' OR tem_deficiencia = 'Sim' 
                                 OR precisa_cuidados_especiais = 'Sim')
                                 ORDER BY nome_pessoa""", (cadastro['id'],))
                pessoas_saude = cursor.fetchall()
                if pessoas_saude:
                    dados.append({'cadastro': cadastro, 'pessoas_saude': pessoas_saude})
            
            logger.info(f"📊 Encontrados {len(dados)} cadastros com dados de saúde")
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
                         AVG(renda_familiar) as renda_media
                         FROM cadastros 
                         WHERE bairro IS NOT NULL AND bairro != ''
                         GROUP BY bairro 
                         ORDER BY total DESC''')
        dados = cursor.fetchall()
        filename = 'relatorio_por_bairro'
    elif tipo == 'renda':
        # Buscar faixas de renda
        cursor.execute('''SELECT 
            CASE 
                WHEN renda_familiar IS NOT NULL AND renda_familiar <= 1000 THEN 'Até R$ 1.000'
                WHEN renda_familiar IS NOT NULL AND renda_familiar BETWEEN 1001 AND 2000 THEN 'R$ 1.001 - R$ 2.000'
                WHEN renda_familiar IS NOT NULL AND renda_familiar BETWEEN 2001 AND 3000 THEN 'R$ 2.001 - R$ 3.000'
                WHEN renda_familiar IS NOT NULL AND renda_familiar > 3000 THEN 'Acima de R$ 3.000'
                ELSE 'Não informado'
            END as faixa_renda,
            COUNT(*) 
            FROM cadastros 
            GROUP BY faixa_renda''')
        faixas_renda = cursor.fetchall()
        
        # Buscar renda por bairro
        cursor.execute('''SELECT bairro, 
                         AVG(renda_familiar) as renda_media, 
                         COUNT(*) as total
                         FROM cadastros 
                         WHERE bairro IS NOT NULL AND bairro != ''
                         GROUP BY bairro 
                         ORDER BY renda_media DESC NULLS LAST''')
        renda_bairro = cursor.fetchall()
        
        # Combinar dados para exportação
        dados = {
            'faixas_renda': faixas_renda,
            'renda_bairro': renda_bairro
        }
        filename = 'relatorio_renda'
    elif tipo == 'caixa':
        logger.info("💰 Buscando dados do caixa para exportação")
        filtro_tipo = request.args.get('filtro_tipo')  # 'entrada' ou 'saida'
        
        # Query base
        query = '''SELECT mc.id, mc.tipo, mc.valor, mc.descricao, mc.cadastro_id, 
                   mc.nome_pessoa, mc.numero_recibo, mc.observacoes, mc.data_movimentacao, 
                   mc.usuario, c.nome_completo as titular_cadastro
                   FROM movimentacoes_caixa mc
                   LEFT JOIN cadastros c ON mc.cadastro_id = c.id'''
        
        # Adicionar filtro se especificado
        if filtro_tipo in ['entrada', 'saida']:
            query += f" WHERE mc.tipo = '{filtro_tipo}'"
            filename = f'relatorio_caixa_{filtro_tipo}'
        else:
            filename = 'relatorio_caixa'
            
        query += ' ORDER BY mc.data_movimentacao DESC'
        
        cursor.execute(query)
        dados = cursor.fetchall()
        logger.info(f"📊 Encontradas {len(dados)} movimentações para exportação")
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
            writer.writerow(['Titular', 'Idade', 'Telefone', 'Bairro', 'Pessoa', 'Doença Crônica', 'Doenças', 
                           'Medicamento Contínuo', 'Medicamentos', 'Doença Mental', 'Doenças Mentais',
                           'Deficiência', 'Deficiências', 'Cuidados Especiais', 'Cuidados'])
            for item in dados:
                cadastro = item['cadastro']
                for pessoa in item['pessoas_saude']:
                    writer.writerow([
                        cadastro['nome_completo'],
                        cadastro['idade'] or '',
                        cadastro['telefone'] or '',
                        cadastro['bairro'] or '',
                        pessoa['nome_pessoa'],
                        pessoa['tem_doenca_cronica'],
                        pessoa['doencas_cronicas'] or '',
                        pessoa['usa_medicamento_continuo'],
                        pessoa['medicamentos'] or '',
                        pessoa['tem_doenca_mental'],
                        pessoa['doencas_mentais'] or '',
                        pessoa['tem_deficiencia'],
                        pessoa['deficiencias'] or '',
                        pessoa['precisa_cuidados_especiais'],
                        pessoa['cuidados_especiais'] or ''
                    ])
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
            writer.writerow(['=== ANÁLISE DE RENDA FAMILIAR ==='])
            writer.writerow([''])
            writer.writerow(['=== POR FAIXA DE RENDA ==='])
            writer.writerow(['Faixa de Renda', 'Total de Cadastros'])
            for row in dados['faixas_renda']:
                writer.writerow([row[0] or 'Não informado', row[1]])
            writer.writerow([''])
            writer.writerow(['=== RENDA POR BAIRRO ==='])
            writer.writerow(['Bairro', 'Renda Média', 'Total de Cadastros'])
            for row in dados['renda_bairro']:
                writer.writerow([row[0] or 'Não informado', f"R$ {row[1]:.2f}" if row[1] else 'Não informado', row[2]])
        elif tipo == 'caixa':
            writer.writerow(['ID', 'Tipo', 'Valor', 'Descrição', 'Titular Cadastro', 'Nome Pessoa', 
                           'Número Recibo', 'Observações', 'Data', 'Usuário'])
            for row in dados:
                writer.writerow([
                    row['id'],
                    row['tipo'].title(),
                    f"R$ {row['valor']:.2f}",
                    row['descricao'] or '',
                    row['titular_cadastro'] or '',
                    row['nome_pessoa'] or '',
                    row['numero_recibo'] or '',
                    row['observacoes'] or '',
                    row['data_movimentacao'].strftime('%d/%m/%Y %H:%M') if row['data_movimentacao'] else '',
                    row['usuario'] or ''
                ])
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
        logger.info("📄 Iniciando geração de PDF")
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        
        logger.info("📦 Criando buffer e documento PDF")
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        # Título
        logger.info(f"📝 Criando título para tipo={tipo}, cadastro_id={cadastro_id}")
        if tipo == 'completo':
            title = Paragraph("AMEG - Relatório Completo de Cadastros", styles['Title'])
        elif tipo == 'simplificado':
            title = Paragraph("AMEG - Relatório Simplificado", styles['Title'])
        elif tipo == 'saude':
            if cadastro_id:
                title = Paragraph("AMEG - Relatório de Saúde Individual", styles['Title'])
            else:
                title = Paragraph("AMEG - Relatório de Saúde", styles['Title'])
        elif tipo == 'estatistico':
            title = Paragraph("AMEG - Relatório Estatístico", styles['Title'])
        elif tipo == 'bairro':
            title = Paragraph("AMEG - Relatório por Bairro", styles['Title'])
        elif tipo == 'renda':
            title = Paragraph("AMEG - Análise de Renda Familiar", styles['Title'])
        elif tipo == 'caixa':
            filtro_tipo = request.args.get('filtro_tipo')
            if filtro_tipo == 'entrada':
                title = Paragraph("AMEG - Relatório de Entradas do Caixa", styles['Title'])
            elif filtro_tipo == 'saida':
                title = Paragraph("AMEG - Relatório de Saídas do Caixa", styles['Title'])
            else:
                title = Paragraph("AMEG - Relatório de Movimentações do Caixa", styles['Title'])
        else:
            title = Paragraph("AMEG - Relatório Geral", styles['Title'])
        
        logger.info("✅ Título criado, adicionando aos elementos")
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        # Adicionar subtítulo para relatório individual de saúde
        if tipo == 'saude' and cadastro_id:
            subtitle = Paragraph(f"<i>Relatório detalhado de condições de saúde - Cadastro ID: {cadastro_id}</i>", styles['Normal'])
            elements.append(subtitle)
            elements.append(Spacer(1, 8))
        
        # Dados da tabela
        logger.info(f"🔧 Preparando dados da tabela para tipo={tipo}")
        if tipo == 'simplificado':
            logger.info("📊 Processando dados simplificados")
            table_data = [['Nome', 'Telefone', 'Bairro', 'Renda']]
            for row in dados:
                table_data.append([
                    str(row[0] or ''),
                    str(row[1] or ''),
                    str(row[2] or ''),
                    f"R$ {row[3] or '0'}" if row[3] else 'Não informado'
                ])
        elif tipo == 'saude':
            logger.info("🏥 Processando dados de saúde")
            
            # Criar múltiplas tabelas para melhor visualização
            for i, row in enumerate(dados):
                logger.info(f"📋 Registro {i+1}: {dict(row) if hasattr(row, 'keys') else row}")
                
                # Extrair dados do cadastro
                cadastro = row['cadastro']
                pessoas_saude = row['pessoas_saude']
                
                # Tabela 1: Dados Pessoais
                pessoais_title = Paragraph(f"<b>👤 {cadastro['nome_completo'] or 'Não informado'}</b>", styles['Heading3'])
                elements.append(pessoais_title)
                elements.append(Spacer(1, 6))
                
                pessoais_data = [
                    ['Idade', f"{cadastro['idade']} anos" if cadastro['idade'] else 'Não informado'],
                    ['Telefone', str(cadastro['telefone'] or 'Não informado')],
                    ['Bairro', str(cadastro['bairro'] or 'Não informado')]
                ]
                
                pessoais_table = Table(pessoais_data, colWidths=[2*inch, 4*inch])
                pessoais_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6)
                ]))
                elements.append(pessoais_table)
                elements.append(Spacer(1, 12))
                
                # Tabela 2: Condições de Saúde por Pessoa
                saude_title = Paragraph("<b>🏥 Condições de Saúde por Pessoa</b>", styles['Heading3'])
                elements.append(saude_title)
                elements.append(Spacer(1, 6))
                
                # Para cada pessoa com condições de saúde
                for j, pessoa in enumerate(pessoas_saude):
                    # Nome da pessoa
                    pessoa_title = Paragraph(f"<b>Pessoa {j+1}: {pessoa['nome_pessoa']}</b>", styles['Heading4'])
                    elements.append(pessoa_title)
                    elements.append(Spacer(1, 4))
                    
                    # Dados de saúde da pessoa
                    pessoa_saude_data = []
                    
                    # Doenças Crônicas
                    if pessoa['tem_doenca_cronica'] == 'Sim':
                        pessoa_saude_data.append(['Doenças Crônicas', str(pessoa['doencas_cronicas'] or 'Não especificado')])
                    
                    # Medicamentos
                    if pessoa['usa_medicamento_continuo'] == 'Sim':
                        pessoa_saude_data.append(['Medicamentos Contínuos', str(pessoa['medicamentos'] or 'Não especificado')])
                    
                    # Doenças Mentais
                    if pessoa['tem_doenca_mental'] == 'Sim':
                        pessoa_saude_data.append(['Condições Mentais', str(pessoa['doencas_mentais'] or 'Não especificado')])
                    
                    # Deficiências
                    if pessoa['tem_deficiencia'] == 'Sim':
                        pessoa_saude_data.append(['Deficiências', str(pessoa['deficiencias'] or 'Não especificado')])
                    
                    # Cuidados Especiais
                    if pessoa['precisa_cuidados_especiais'] == 'Sim':
                        pessoa_saude_data.append(['Cuidados Especiais', str(pessoa['cuidados_especiais'] or 'Não especificado')])
                    
                    if pessoa_saude_data:
                        pessoa_table = Table(pessoa_saude_data, colWidths=[2.5*inch, 4.5*inch])
                        pessoa_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (0, -1), colors.lightcoral),
                            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                            ('FONTSIZE', (0, 0), (-1, -1), 9),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ('LEFTPADDING', (0, 0), (-1, -1), 8),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                            ('TOPPADDING', (0, 0), (-1, -1), 6),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 6)
                        ]))
                        elements.append(pessoa_table)
                        elements.append(Spacer(1, 8))
                
                # Adicionar espaço entre registros se houver mais de um
                if i < len(dados) - 1:
                    elements.append(Spacer(1, 20))
                    elements.append(Paragraph("<hr/>", styles['Normal']))
                    elements.append(Spacer(1, 20))
            
            # Não criar tabela adicional, pois já criamos as tabelas acima
            table_data = None
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
            # Por Faixa de Renda
            faixa_para = Paragraph("<b>💰 Por Faixa de Renda</b>", styles['Heading3'])
            elements.append(faixa_para)
            elements.append(Spacer(1, 6))
            
            table_data = [['Faixa de Renda', 'Total de Cadastros']]
            for row in dados['faixas_renda']:
                table_data.append([
                    str(row[0] or 'Não informado'),
                    str(row[1] or '0')
                ])
            
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
            
            # Por Bairro
            bairro_para = Paragraph("<b>📍 Renda por Bairro</b>", styles['Heading3'])
            elements.append(bairro_para)
            elements.append(Spacer(1, 6))
            
            table_data = [['Bairro', 'Renda Média', 'Total de Cadastros']]
            for row in dados['renda_bairro']:
                table_data.append([
                    str(row[0] or 'Não informado'),
                    f"R$ {row[1]:.2f}" if row[1] else 'Não informado',
                    str(row[2] or '0')
                ])
            
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
        elif tipo == 'caixa':
            logger.info("💰 Processando dados do caixa para PDF")
            filtro_tipo = request.args.get('filtro_tipo')
            
            # Calcular totais baseado no filtro
            if filtro_tipo == 'entrada':
                total_entradas = sum(row['valor'] for row in dados)
                total_saidas = 0
                saldo_total = total_entradas
            elif filtro_tipo == 'saida':
                total_saidas = sum(row['valor'] for row in dados)
                total_entradas = 0
                saldo_total = -total_saidas
            else:
                total_entradas = sum(row['valor'] for row in dados if row['tipo'] == 'entrada')
                total_saidas = sum(row['valor'] for row in dados if row['tipo'] == 'saida')
                saldo_total = total_entradas - total_saidas
            
            # Resumo financeiro
            if filtro_tipo == 'entrada':
                resumo_para = Paragraph("<b>💰 Resumo de Entradas</b>", styles['Heading3'])
                resumo_data = [
                    ['Total de Entradas:', f"R$ {total_entradas:.2f}"],
                    ['Quantidade de Registros:', str(len(dados))]
                ]
            elif filtro_tipo == 'saida':
                resumo_para = Paragraph("<b>💰 Resumo de Saídas</b>", styles['Heading3'])
                resumo_data = [
                    ['Total de Saídas:', f"R$ {total_saidas:.2f}"],
                    ['Quantidade de Registros:', str(len(dados))]
                ]
            else:
                resumo_para = Paragraph("<b>💰 Resumo Financeiro</b>", styles['Heading3'])
                resumo_data = [
                    ['Total de Entradas:', f"R$ {total_entradas:.2f}"],
                    ['Total de Saídas:', f"R$ {total_saidas:.2f}"],
                    ['Saldo Atual:', f"R$ {saldo_total:.2f}"]
                ]
            
            elements.append(resumo_para)
            elements.append(Spacer(1, 6))
            
            resumo_table = Table(resumo_data, colWidths=[3*inch, 2*inch])
            resumo_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT')
            ]))
            elements.append(resumo_table)
            elements.append(Spacer(1, 20))
            
            # Movimentações detalhadas
            if filtro_tipo == 'entrada':
                movimentacoes_para = Paragraph("<b>📈 Entradas Detalhadas</b>", styles['Heading3'])
            elif filtro_tipo == 'saida':
                movimentacoes_para = Paragraph("<b>📉 Saídas Detalhadas</b>", styles['Heading3'])
            else:
                movimentacoes_para = Paragraph("<b>📋 Movimentações Detalhadas</b>", styles['Heading3'])
            
            elements.append(movimentacoes_para)
            elements.append(Spacer(1, 6))
            
            table_data = [['Data', 'Tipo', 'Valor', 'Descrição', 'Pessoa', 'Usuário']]
            for row in dados:
                table_data.append([
                    row['data_movimentacao'].strftime('%d/%m/%Y') if row['data_movimentacao'] else '',
                    row['tipo'].title(),
                    f"R$ {row['valor']:.2f}",
                    str(row['descricao'] or '')[:30] + ('...' if len(str(row['descricao'] or '')) > 30 else ''),
                    str(row['nome_pessoa'] or row['titular_cadastro'] or '')[:20] + ('...' if len(str(row['nome_pessoa'] or row['titular_cadastro'] or '')) > 20 else ''),
                    str(row['usuario'] or '')
                ])
            
            table = Table(table_data, colWidths=[1*inch, 0.8*inch, 1*inch, 2*inch, 1.5*inch, 0.7*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP')
            ]))
            elements.append(table)
            
            # Não criar tabela adicional, pois já criamos as tabelas acima
            table_data = None
        else:  # completo
            if cadastro_id:
                # PDF detalhado para um cadastro específico com TODOS os campos
                for row in dados:
                    # Título do cadastro
                    nome_para = Paragraph(f"<b>Cadastro: {row['nome_completo'] or 'Não informado'}</b>", styles['Heading2'])
                    elements.append(nome_para)
                    elements.append(Spacer(1, 12))
                    
                    # Dados Pessoais
                    pessoais_para = Paragraph("<b>📋 Dados Pessoais</b>", styles['Heading3'])
                    elements.append(pessoais_para)
                    elements.append(Spacer(1, 6))
                    
                    pessoais_data = [
                        ['Nome Completo:', str(row['nome_completo'] or '')],
                        ['Endereço:', f"{row['endereco'] or ''}, {row['numero'] or ''}"],
                        ['Bairro:', str(row['bairro'] or '')],
                        ['CEP:', str(row['cep'] or '')],
                        ['Telefone:', str(row['telefone'] or '')],
                        ['Ponto Referência:', str(row['ponto_referencia'] or '')],
                        ['Gênero:', str(row['genero'] or '')],
                        ['Idade:', str(row['idade'] or '')],
                        ['Data Nascimento:', str(row['data_nascimento'] or '')],
                        ['Título Eleitor:', str(row['titulo_eleitor'] or '')],
                        ['Cidade Título:', str(row['cidade_titulo'] or '')],
                        ['CPF:', str(row['cpf'] or '')],
                        ['RG:', str(row['rg'] or '')],
                        ['NIS:', str(row['nis'] or '')],
                        ['Estado Civil:', str(row['estado_civil'] or '')],
                        ['Escolaridade:', str(row['escolaridade'] or '')],
                        ['Profissão:', str(row['profissao'] or '')]
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
                    if row['nome_companheiro']:  # Se tem companheiro
                        comp_para = Paragraph("<b>💑 Dados do Companheiro(a)</b>", styles['Heading3'])
                        elements.append(comp_para)
                        elements.append(Spacer(1, 6))
                        
                        comp_data = [
                            ['Nome Companheiro:', str(row['nome_companheiro'] or '')],
                            ['CPF Companheiro:', str(row['cpf_companheiro'] or '')],
                            ['RG Companheiro:', str(row['rg_companheiro'] or '')],
                            ['Idade Companheiro:', str(row['idade_companheiro'] or '')],
                            ['Escolaridade Companheiro:', str(row['escolaridade_companheiro'] or '')],
                            ['Profissão Companheiro:', str(row['profissao_companheiro'] or '')],
                            ['Data Nasc. Companheiro:', str(row['data_nascimento_companheiro'] or '')],
                            ['Título Companheiro:', str(row['titulo_companheiro'] or '')],
                            ['Cidade Título Comp.:', str(row['cidade_titulo_companheiro'] or '')],
                            ['NIS Companheiro:', str(row['nis_companheiro'] or '')]
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
                        ['Tipo Trabalho:', str(row['tipo_trabalho'] or '')],
                        ['Pessoas Trabalham:', str(row['pessoas_trabalham'] or '')],
                        ['Aposentados/Pensionistas:', str(row['aposentados_pensionistas'] or '')],
                        ['Pessoas na Família:', str(row['num_pessoas_familia'] or '')],
                        ['Número Famílias:', str(row['num_familias'] or '')],
                        ['Adultos:', str(row['adultos'] or '')],
                        ['Crianças:', str(row['criancas'] or '')],
                        ['Adolescentes:', str(row['adolescentes'] or '')],
                        ['Idosos:', str(row['idosos'] or '')],
                        ['Gestantes:', str(row['gestantes'] or '')],
                        ['Nutrizes:', str(row['nutrizes'] or '')],
                        ['Renda Familiar:', f"R$ {row['renda_familiar'] or '0'}"],
                        ['Renda Per Capita:', f"R$ {row['renda_per_capita'] or '0'}"],
                        ['Bolsa Família:', f"R$ {row['bolsa_familia'] or '0'}"]
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
                        ['Tipo Casa:', str(row['casa_tipo'] or '')],
                        ['Material Casa:', str(row['casa_material'] or '')],
                        ['Energia:', str(row['energia'] or '')],
                        ['Lixo:', str(row['lixo'] or '')],
                        ['Água:', str(row['agua'] or '')],
                        ['Esgoto:', str(row['esgoto'] or '')]
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
        
        # Criar tabela (exceto para estatístico, renda, cadastro completo individual e saúde que já criou suas tabelas)
        logger.info(f"🔧 Verificando se deve criar tabela: tipo={tipo}, cadastro_id={cadastro_id}, table_data={table_data is not None}")
        if table_data is not None and tipo not in ['estatistico', 'renda'] and not (tipo == 'completo' and cadastro_id):
            logger.info(f"📊 Criando tabela com {len(table_data)} linhas")
            logger.info(f"📋 Cabeçalho da tabela: {table_data[0] if table_data else 'Vazio'}")
            table = Table(table_data)
            
            # Estilo específico para relatório de saúde com mais colunas
            if tipo == 'saude':
                logger.info("🎨 Aplicando estilo para tabela de saúde")
                # Definir larguras das colunas para melhor layout
                col_widths = [2.2*inch, 0.8*inch, 1.2*inch, 1.2*inch, 1.8*inch, 1.8*inch, 1.5*inch, 1.5*inch, 1.5*inch]
                table = Table(table_data, colWidths=col_widths)
                table.setStyle(TableStyle([
                    # Cabeçalho
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                    ('TOPPADDING', (0, 0), (-1, 0), 10),
                    
                    # Dados
                    ('ALIGN', (0, 1), (0, -1), 'LEFT'),    # Nome - esquerda
                    ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # Idade - centro
                    ('ALIGN', (2, 1), (2, -1), 'CENTER'),  # Telefone - centro
                    ('ALIGN', (3, 1), (3, -1), 'LEFT'),    # Bairro - esquerda
                    ('ALIGN', (4, 1), (-1, -1), 'LEFT'),   # Campos de saúde - esquerda
                    
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('TOPPADDING', (0, 1), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                    ('LEFTPADDING', (0, 0), (-1, -1), 4),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                    
                    # Cores alternadas nas linhas
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                    
                    # Bordas
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('LINEBELOW', (0, 0), (-1, 0), 2, colors.darkblue),
                    
                    # Quebra de linha e alinhamento vertical
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('WORDWRAP', (0, 0), (-1, -1), True)
                ]))
            else:
                logger.info("🎨 Aplicando estilo padrão para tabela")
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
            logger.info("✅ Adicionando tabela aos elementos do PDF")
            elements.append(table)
        else:
            logger.info(f"⚠️ Tabela NÃO será criada: tipo={tipo}, cadastro_id={cadastro_id}, condição: {tipo not in ['estatistico', 'renda'] and not (tipo == 'completo' and cadastro_id)}")
        
        logger.info(f"🔨 Construindo PDF com {len(elements)} elementos")
        doc.build(elements)
        
        buffer.seek(0)
        logger.info(f"✅ PDF gerado com sucesso: {filename}.pdf")
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
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT nome_arquivo, arquivo_dados, tipo_arquivo FROM arquivos_saude WHERE id = %s', (arquivo_id,))
        arquivo = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not arquivo or not arquivo['arquivo_dados']:
            flash('Arquivo não encontrado!')
            return redirect(url_for('arquivos_cadastros'))
        
        # Criar um objeto BytesIO com os dados do arquivo
        file_data = io.BytesIO(arquivo['arquivo_dados'])
        
        return send_file(
            file_data,
            as_attachment=True,
            download_name=arquivo['nome_arquivo'],
            mimetype='application/octet-stream'
        )
        
    except Exception as e:
        logger.error(f"Erro ao baixar arquivo {arquivo_id}: {e}")
        flash('Erro ao baixar arquivo!')
        return redirect(url_for('arquivos_cadastros'))

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
    if not is_admin_user(session['usuario']):
        flash('Acesso negado! Apenas administradores podem gerenciar usuários.')
        return redirect(url_for('dashboard'))
    
    logger.info("📋 Carregando lista de usuários...")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, usuario, COALESCE(tipo, \'usuario\') as tipo FROM usuarios ORDER BY usuario')
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

def validar_senha(senha):
    """Valida se a senha atende aos requisitos de segurança"""
    import re
    
    if len(senha) < 8:
        return False, "Senha deve ter pelo menos 8 caracteres"
    
    if not re.search(r'[A-Z]', senha):
        return False, "Senha deve conter pelo menos uma letra maiúscula"
    
    if not re.search(r'[a-z]', senha):
        return False, "Senha deve conter pelo menos uma letra minúscula"
    
    if not re.search(r'[0-9]', senha):
        return False, "Senha deve conter pelo menos um número"
    
    return True, "Senha válida"

@app.route('/criar_usuario', methods=['POST'])
def salvar_usuario():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    if session['usuario'] != 'admin':
        flash('Acesso negado! Apenas administradores podem criar usuários.')
        return redirect(url_for('dashboard'))
    
    novo_usuario = request.form['usuario']
    nova_senha = request.form['senha']
    tipo_usuario = request.form.get('tipo', 'usuario')
    
    # Validar senha
    senha_valida, mensagem = validar_senha(nova_senha)
    if not senha_valida:
        flash(f'Erro na senha: {mensagem}')
        return redirect(url_for('criar_usuario'))
    
    logger.info(f"👤 Criando novo usuário: {novo_usuario} (tipo: {tipo_usuario})")
    
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
        cursor.execute('INSERT INTO usuarios (usuario, senha, tipo) VALUES (%s, %s, %s) RETURNING id', (novo_usuario, senha_hash, tipo_usuario))
        usuario_id = cursor.fetchone()[0]
        logger.debug("Query INSERT executada")
        
        # Processar permissões adicionais
        permissoes = request.form.getlist('permissoes')
        logger.info(f"Permissões selecionadas: {permissoes}")
        
        for permissao in permissoes:
            adicionar_permissao_usuario(usuario_id, permissao)
            logger.info(f"Permissão '{permissao}' adicionada ao usuário {novo_usuario}")
        
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
    if not is_admin_user(session['usuario']):
        flash('Acesso negado! Apenas administradores podem excluir usuários.')
        return redirect(url_for('dashboard'))
    
    # Proteção especial para admin ID 1
    if usuario_id == 1:
        flash('Erro! O usuário admin principal (ID 1) não pode ser excluído.')
        return redirect(url_for('usuarios'))
    
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

@app.route('/promover_usuario/<int:usuario_id>')
def promover_usuario(usuario_id):
    if 'usuario' not in session:
        return redirect(url_for('login'))
    if not is_admin_user(session['usuario']):
        flash('Acesso negado! Apenas administradores podem promover usuários.')
        return redirect(url_for('dashboard'))
    
    # Proteção especial para admin ID 1
    if usuario_id == 1:
        flash('O usuário admin principal (ID 1) já possui privilégios máximos.')
        return redirect(url_for('usuarios'))
    
    logger.info(f"👑 Tentando promover usuário ID: {usuario_id}")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar se usuário existe
        cursor.execute('SELECT usuario, tipo FROM usuarios WHERE id = %s', (usuario_id,))
        user_data = cursor.fetchone()
        
        if not user_data:
            logger.warning(f"⚠️ Usuário ID {usuario_id} não encontrado")
            flash('Usuário não encontrado!')
            cursor.close()
            conn.close()
            return redirect(url_for('usuarios'))
        
        username = user_data[0]
        tipo_atual = user_data[1] if len(user_data) > 1 else 'usuario'
        
        if tipo_atual == 'admin':
            logger.warning(f"⚠️ Usuário {username} já é administrador")
            flash(f'Usuário "{username}" já é administrador!')
            cursor.close()
            conn.close()
            return redirect(url_for('usuarios'))
        
        # Promover usuário a admin
        cursor.execute('UPDATE usuarios SET tipo = %s WHERE id = %s', ('admin', usuario_id))
        usuarios_atualizados = cursor.rowcount
        
        if usuarios_atualizados > 0:
            conn.commit()
            logger.info(f"✅ Usuário {username} (ID: {usuario_id}) promovido a administrador")
            flash(f'Usuário "{username}" promovido a administrador com sucesso!')
        else:
            logger.warning(f"⚠️ Nenhum usuário foi atualizado (ID: {usuario_id})")
            flash('Erro: Usuário não foi promovido.')
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ Erro ao promover usuário ID {usuario_id}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        flash(f'Erro ao promover usuário: {str(e)}')
    
    return redirect(url_for('usuarios'))

@app.route('/rebaixar_usuario/<int:usuario_id>')
def rebaixar_usuario(usuario_id):
    if 'usuario' not in session:
        return redirect(url_for('login'))
    if not is_admin_user(session['usuario']):
        flash('Acesso negado! Apenas administradores podem rebaixar usuários.')
        return redirect(url_for('dashboard'))
    
    # Proteção especial para admin ID 1
    if usuario_id == 1:
        flash('Erro! O usuário admin principal (ID 1) não pode ser rebaixado.')
        return redirect(url_for('usuarios'))
    
    logger.info(f"👤 Tentando rebaixar usuário ID: {usuario_id}")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar se usuário existe
        cursor.execute('SELECT usuario, tipo FROM usuarios WHERE id = %s', (usuario_id,))
        user_data = cursor.fetchone()
        
        if not user_data:
            logger.warning(f"⚠️ Usuário ID {usuario_id} não encontrado")
            flash('Usuário não encontrado!')
            cursor.close()
            conn.close()
            return redirect(url_for('usuarios'))
        
        username = user_data[0]
        tipo_atual = user_data[1] if len(user_data) > 1 else 'usuario'
        
        if username == 'admin':
            logger.warning("⚠️ Tentativa de rebaixar usuário admin principal bloqueada")
            flash('Não é possível rebaixar o usuário admin principal!')
            cursor.close()
            conn.close()
            return redirect(url_for('usuarios'))
        
        if tipo_atual == 'usuario':
            logger.warning(f"⚠️ Usuário {username} já é usuário comum")
            flash(f'Usuário "{username}" já é usuário comum!')
            cursor.close()
            conn.close()
            return redirect(url_for('usuarios'))
        
        # Rebaixar usuário para comum
        cursor.execute('UPDATE usuarios SET tipo = %s WHERE id = %s', ('usuario', usuario_id))
        usuarios_atualizados = cursor.rowcount
        
        if usuarios_atualizados > 0:
            conn.commit()
            logger.info(f"✅ Usuário {username} (ID: {usuario_id}) rebaixado a usuário comum")
            flash(f'Usuário "{username}" rebaixado a usuário comum!')
        else:
            logger.warning(f"⚠️ Nenhum usuário foi atualizado (ID: {usuario_id})")
            flash('Erro: Usuário não foi rebaixado.')
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ Erro ao rebaixar usuário ID {usuario_id}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        flash(f'Erro ao rebaixar usuário: {str(e)}')
    
    return redirect(url_for('usuarios'))

@app.route('/editar_usuario/<int:usuario_id>', methods=['GET', 'POST'])
def editar_usuario(usuario_id):
    if 'usuario' not in session:
        return redirect(url_for('login'))
    if not is_admin_user(session['usuario']):
        flash('Acesso negado! Apenas administradores podem editar usuários.')
        return redirect(url_for('dashboard'))
    
    # Proteção especial para admin ID 1
    if usuario_id == 1:
        # Buscar dados do usuário admin para verificar
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT usuario FROM usuarios WHERE id = 1')
        admin_data = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if admin_data and session['usuario'] != admin_data[0]:
            flash('Acesso negado! Apenas o próprio usuário admin pode alterar sua senha.')
            return redirect(url_for('usuarios'))
    
    logger.info(f"✏️ Editando usuário ID: {usuario_id}")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if request.method == 'GET':
            # Buscar dados do usuário
            cursor.execute('SELECT id, usuario, COALESCE(tipo, \'usuario\') as tipo FROM usuarios WHERE id = %s', (usuario_id,))
            user_data = cursor.fetchone()
            
            if not user_data:
                flash('Usuário não encontrado!')
                cursor.close()
                conn.close()
                return redirect(url_for('usuarios'))
            
            # Buscar permissões do usuário
            permissoes_usuario = obter_permissoes_usuario(usuario_id)
            
            cursor.close()
            conn.close()
            return render_template('editar_usuario.html', 
                                 usuario=user_data, 
                                 permissoes_usuario=permissoes_usuario)
        
        elif request.method == 'POST':
            # Processar edição
            novo_tipo = request.form.get('tipo', 'usuario')
            nova_senha = request.form.get('nova_senha', '').strip()
            
            # Buscar dados atuais
            cursor.execute('SELECT usuario, tipo FROM usuarios WHERE id = %s', (usuario_id,))
            user_data = cursor.fetchone()
            
            if not user_data:
                flash('Usuário não encontrado!')
                cursor.close()
                conn.close()
                return redirect(url_for('usuarios'))
            
            username = user_data[0]
            
            # Proteger admin principal
            if username == 'admin' and novo_tipo != 'admin':
                flash('Não é possível alterar o tipo do usuário admin principal!')
                cursor.close()
                conn.close()
                return redirect(url_for('usuarios'))
            
            # Atualizar tipo
            cursor.execute('UPDATE usuarios SET tipo = %s WHERE id = %s', (novo_tipo, usuario_id))
            logger.info(f"✅ Tipo do usuário {username} atualizado para {novo_tipo}")
            
            # Processar permissões adicionais
            permissoes_atuais = obter_permissoes_usuario(usuario_id)
            permissoes_novas = request.form.getlist('permissoes')
            
            # Remover permissões que não estão mais selecionadas
            for permissao in permissoes_atuais:
                if permissao not in permissoes_novas:
                    remover_permissao_usuario(usuario_id, permissao)
                    logger.info(f"Permissão '{permissao}' removida do usuário {username}")
            
            # Adicionar novas permissões
            for permissao in permissoes_novas:
                if permissao not in permissoes_atuais:
                    adicionar_permissao_usuario(usuario_id, permissao)
                    logger.info(f"Permissão '{permissao}' adicionada ao usuário {username}")
            
            # Atualizar senha se fornecida
            if nova_senha:
                senha_hash = generate_password_hash(nova_senha)
                cursor.execute('UPDATE usuarios SET senha = %s WHERE id = %s', (senha_hash, usuario_id))
                logger.info(f"✅ Senha do usuário {username} atualizada")
            
            conn.commit()
            cursor.close()
            conn.close()
            
            flash(f'Usuário "{username}" atualizado com sucesso!')
            return redirect(url_for('usuarios'))
            
    except Exception as e:
        logger.error(f"❌ Erro ao editar usuário ID {usuario_id}: {e}")
        flash(f'Erro ao editar usuário: {str(e)}')
        return redirect(url_for('usuarios'))

@app.route('/editar_cadastro/<int:cadastro_id>')
def editar_cadastro(cadastro_id):
    if 'usuario' not in session:
        logger.debug("Usuário não logado tentando acessar /editar_cadastro")
        return redirect(url_for('login'))
    
    logger.info(f"📝 Carregando cadastro para edição: ID {cadastro_id}")
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        logger.debug(f"Buscando cadastro ID {cadastro_id}")
        
        cursor.execute('SELECT *, foto_base64 FROM cadastros WHERE id = %s', (cadastro_id,))
        
        cadastro = cursor.fetchone()
        logger.debug(f"Cadastro encontrado: {cadastro is not None}")
        
        if cadastro:
            foto_presente = cadastro.get('foto_base64') is not None
            foto_tamanho = len(cadastro.get('foto_base64', '')) if cadastro.get('foto_base64') else 0
            logger.debug(f"Foto presente: {foto_presente}")
            logger.debug(f"Tamanho da foto: {foto_tamanho} caracteres")
            if foto_presente and foto_tamanho > 0:
                logger.debug(f"Primeiros 50 chars da foto: {cadastro.get('foto_base64', '')[:50]}...")
            else:
                logger.warning("⚠️ Campo foto_base64 está vazio ou nulo")
        
        # Buscar arquivos de saúde associados
        arquivos_saude = []
        dados_saude_pessoas = []
        if cadastro:
            logger.debug("Buscando arquivos de saúde...")
            cursor.execute('SELECT id, nome_arquivo, tipo_arquivo, descricao, data_upload FROM arquivos_saude WHERE cadastro_id = %s ORDER BY data_upload DESC', (cadastro_id,))
            arquivos_saude = cursor.fetchall()
            logger.debug(f"Arquivos encontrados: {len(arquivos_saude)}")
            
            # Buscar dados de saúde por pessoa
            logger.debug("Buscando dados de saúde por pessoa...")
            cursor.execute('SELECT * FROM dados_saude_pessoa WHERE cadastro_id = %s ORDER BY id', (cadastro_id,))
            dados_saude_pessoas = cursor.fetchall()
            logger.debug(f"Dados de saúde encontrados para {len(dados_saude_pessoas)} pessoas")
            logger.debug(f"Encontrados {len(arquivos_saude)} arquivos de saúde")
        
        cursor.close()
        conn.close()
        logger.info("✅ Cadastro e arquivos carregados para edição")
        
        if not cadastro:
            logger.warning(f"⚠️ Cadastro ID {cadastro_id} não encontrado")
            flash('Cadastro não encontrado!')
            return redirect(url_for('dashboard'))
        
        return render_template('editar_cadastro.html', cadastro=cadastro, arquivos_saude=arquivos_saude, dados_saude_pessoas=dados_saude_pessoas)
        
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
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Buscar o cadastro_id antes de excluir
        cursor.execute('SELECT cadastro_id FROM arquivos_saude WHERE id = %s', (arquivo_id,))
        
        result = cursor.fetchone()
        if not result:
            flash('Arquivo não encontrado!')
            return redirect(url_for('dashboard'))
        
        cadastro_id = result[0] if isinstance(result, tuple) else result['cadastro_id']
        
        # Excluir o arquivo
        cursor.execute('DELETE FROM arquivos_saude WHERE id = %s', (arquivo_id,))
        
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
        conn = get_db_connection()
        cursor = conn.cursor()
        logger.debug("Conexão PostgreSQL estabelecida")
        
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
            'fonte_renda_outro', 'fonte_renda_outro_desc', 'pessoas_dependem_renda', 'foto_base64'
        ]
        
        logger.debug(f"Total de campos para atualização: {len(campos)}")
        
        # Log específico para foto_base64
        foto_form_value = request.form.get('foto_base64', '')
        logger.debug(f"🖼️ Valor foto_base64 do formulário: {'Presente' if foto_form_value else 'Ausente'}")
        logger.debug(f"🖼️ Tamanho foto_base64: {len(foto_form_value)} caracteres")
        if foto_form_value:
            logger.debug(f"🖼️ Primeiros 50 chars: {foto_form_value[:50]}...")
        
        
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
        set_clauses = [f"{campo} = %s" for campo in campos]
        sql_update = f"""
        UPDATE cadastros SET 
        {', '.join(set_clauses)}
        WHERE id = %s
        """
        
        logger.debug(f"Query UPDATE construída com {len(set_clauses)} campos")
        logger.debug(f"Query: {sql_update[:200]}...")
        
        logger.debug("Executando query UPDATE...")
        cursor.execute(sql_update, valores)
        
        rows_affected = cursor.rowcount
        logger.debug(f"Linhas afetadas: {rows_affected}")
        
        if rows_affected > 0:
            # Upload de novos arquivos usando a mesma conexão
            uploaded_files = []
            for file_type in ['laudo', 'receita', 'imagem']:
                # Processar arrays de arquivos
                files = request.files.getlist(f'{file_type}[]')
                descriptions = request.form.getlist(f'descricao_{file_type}[]')
                
                for i, file in enumerate(files):
                    if file and file.filename and allowed_file(file.filename):
                        logger.debug(f"Processando arquivo: {file.filename} ({file_type})")
                        file_data = file.read()
                        descricao = descriptions[i] if i < len(descriptions) else ''
                        
                        cursor.execute('INSERT INTO arquivos_saude (cadastro_id, nome_arquivo, tipo_arquivo, arquivo_dados, descricao) VALUES (%s, %s, %s, %s, %s)', 
                                    (cadastro_id, file.filename, file_type, file_data, descricao))
                        
                        uploaded_files.append(f"{file_type}: {file.filename}")
                        logger.debug(f"Arquivo {file.filename} salvo com sucesso")
            
            # Processar dados de saúde por pessoa - remover existentes e inserir novos
            logger.debug("Atualizando dados de saúde por pessoa...")
            
            # Remover dados existentes
            cursor.execute('DELETE FROM dados_saude_pessoa WHERE cadastro_id = %s', (cadastro_id,))
            logger.debug("Dados de saúde anteriores removidos")
            
            # Inserir novos dados
            pessoas_saude = []
            for key in request.form.keys():
                if key.startswith('saude_nome_'):
                    pessoa_num = key.split('_')[-1]
                    nome_pessoa = request.form.get(f'saude_nome_{pessoa_num}')
                    
                    if nome_pessoa:  # Só processar se tem nome
                        # Processar checkboxes de condições
                        condicoes = request.form.getlist(f'saude_condicoes_{pessoa_num}[]')
                        
                        dados_pessoa = {
                            'nome_pessoa': nome_pessoa,
                            'tem_doenca_cronica': 'Sim' if 'doenca_cronica' in condicoes else 'Não',
                            'doencas_cronicas': request.form.get(f'saude_doencas_cronicas_{pessoa_num}', ''),
                            'usa_medicamento_continuo': 'Sim' if 'medicamento' in condicoes else 'Não',
                            'medicamentos': request.form.get(f'saude_medicamentos_{pessoa_num}', ''),
                            'tem_doenca_mental': 'Sim' if 'doenca_mental' in condicoes else 'Não',
                            'doencas_mentais': request.form.get(f'saude_doencas_mentais_{pessoa_num}', ''),
                            'tem_deficiencia': 'Sim' if 'deficiencia' in condicoes else 'Não',
                            'deficiencias': request.form.get(f'saude_deficiencias_{pessoa_num}', ''),
                            'precisa_cuidados_especiais': 'Sim' if 'cuidados' in condicoes else 'Não',
                            'cuidados_especiais': request.form.get(f'saude_cuidados_especiais_{pessoa_num}', '')
                        }
                        
                        # Inserir dados de saúde da pessoa
                        cursor.execute('''
                            INSERT INTO dados_saude_pessoa (
                                cadastro_id, nome_pessoa, tem_doenca_cronica, doencas_cronicas,
                                usa_medicamento_continuo, medicamentos, tem_doenca_mental, doencas_mentais,
                                tem_deficiencia, deficiencias, precisa_cuidados_especiais, cuidados_especiais
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ''', (
                            cadastro_id, dados_pessoa['nome_pessoa'], dados_pessoa['tem_doenca_cronica'],
                            dados_pessoa['doencas_cronicas'], dados_pessoa['usa_medicamento_continuo'],
                            dados_pessoa['medicamentos'], dados_pessoa['tem_doenca_mental'],
                            dados_pessoa['doencas_mentais'], dados_pessoa['tem_deficiencia'],
                            dados_pessoa['deficiencias'], dados_pessoa['precisa_cuidados_especiais'],
                            dados_pessoa['cuidados_especiais']
                        ))
                        
                        pessoas_saude.append(nome_pessoa)
                        logger.debug(f"Dados de saúde atualizados para: {nome_pessoa}")
            
            logger.info(f"✅ Dados de saúde atualizados para {len(pessoas_saude)} pessoas")
            
            conn.commit()
            logger.info(f"✅ Cadastro {cadastro_id} atualizado com sucesso")
            
            # Registrar auditoria
            registrar_auditoria(
                usuario=session.get('usuario', 'Sistema'),
                acao='UPDATE',
                tabela='cadastros',
                registro_id=cadastro_id,
                dados_novos=f"Nome: {request.form.get('nome_completo')}, CPF: {request.form.get('cpf')}",
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            
            if uploaded_files:
                flash(f'Cadastro atualizado com sucesso! Novos arquivos: {", ".join(uploaded_files)}')
            else:
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

# Rotas do Sistema de Caixa
@app.route('/caixa')
def caixa():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    # Verificar permissão de caixa
    if not usuario_tem_permissao(session['usuario'], 'caixa'):
        flash('Você não tem permissão para acessar o sistema de caixa', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        logger.info("=== INICIANDO CAIXA ===")
        logger.info(f"Usuário autenticado: {session['usuario']}")
        
        # Obter saldo atual
        logger.info("Tentando obter saldo do caixa...")
        saldo = obter_saldo_caixa()
        logger.info(f"Saldo obtido com sucesso: {saldo}")
        
        # Obter pessoas cadastradas para o select
        logger.info("Tentando obter lista de pessoas cadastradas...")
        pessoas = listar_cadastros_simples()
        logger.info(f"Pessoas obtidas com sucesso: {len(pessoas)} registros")
        
        # Obter últimas movimentações
        logger.info("Tentando obter últimas movimentações...")
        movimentacoes = listar_movimentacoes_caixa(limit=20)
        logger.info(f"Movimentações obtidas com sucesso: {len(movimentacoes)} registros")
        
        logger.info("Renderizando template caixa.html...")
        return render_template('caixa.html', 
                             saldo=saldo, 
                             pessoas=pessoas, 
                             movimentacoes=movimentacoes)
    
    except Exception as e:
        logger.error(f"Erro ao carregar caixa: {e}")
        logger.error(f"Tipo do erro: {type(e)}")
        import traceback
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        flash('Erro ao carregar sistema de caixa', 'error')
        return redirect(url_for('dashboard'))

@app.route('/caixa', methods=['POST'])
def processar_movimentacao_caixa():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    try:
        tipo = request.form.get('tipo')
        valor = float(request.form.get('valor', 0))
        descricao = request.form.get('descricao', '').strip()
        cadastro_id = request.form.get('cadastro_id') or None
        nome_pessoa = request.form.get('nome_pessoa', '').strip()
        numero_recibo = request.form.get('numero_recibo', '').strip()
        observacoes = request.form.get('observacoes', '').strip()
        
        if not descricao:
            flash('Descrição é obrigatória', 'error')
            return redirect(url_for('caixa'))
        
        if valor <= 0:
            flash('Valor deve ser maior que zero', 'error')
            return redirect(url_for('caixa'))
        
        # Inserir movimentação
        movimentacao_id = inserir_movimentacao_caixa(
            tipo, valor, descricao, cadastro_id, nome_pessoa, 
            numero_recibo, observacoes, session['usuario']
        )
        
        # Processar comprovantes se houver
        comprovantes = request.files.getlist('comprovantes')
        logger.info(f"📎 Total de comprovantes recebidos: {len(comprovantes)}")
        
        for i, comprovante in enumerate(comprovantes):
            logger.info(f"📎 Processando comprovante {i+1}: {comprovante.filename if comprovante else 'None'}")
            
            if comprovante and comprovante.filename:
                logger.info(f"  ✅ Arquivo válido: {comprovante.filename}")
                
                # Validar tipo de arquivo
                if not allowed_file(comprovante.filename):
                    logger.warning(f"  ❌ Tipo não permitido: {comprovante.filename}")
                    flash(f'Tipo de arquivo não permitido: {comprovante.filename}', 'error')
                    continue
                
                logger.info(f"  ✅ Tipo permitido: {comprovante.filename}")
                
                # Validar tamanho (16MB máximo)
                comprovante.seek(0, 2)  # Ir para o final
                size = comprovante.tell()
                comprovante.seek(0)  # Voltar ao início
                
                logger.info(f"  📏 Tamanho do arquivo: {size} bytes ({size/1024/1024:.2f} MB)")
                
                if size > 16 * 1024 * 1024:  # 16MB
                    logger.warning(f"  ❌ Arquivo muito grande: {comprovante.filename}")
                    flash(f'Arquivo muito grande: {comprovante.filename}', 'error')
                    continue
                
                # Salvar comprovante
                logger.info(f"  💾 Salvando comprovante: {comprovante.filename}")
                arquivo_dados = comprovante.read()
                inserir_comprovante_caixa(
                    movimentacao_id, 
                    comprovante.filename,
                    comprovante.content_type,
                    arquivo_dados
                )
                logger.info(f"  ✅ Comprovante salvo: {comprovante.filename}")
            else:
                logger.info(f"  ⚠️ Comprovante {i+1} vazio ou sem nome")
        
        flash(f'Movimentação de {tipo} registrada com sucesso!', 'success')
        return redirect(url_for('caixa'))
    
    except Exception as e:
        logger.error(f"Erro ao processar movimentação: {e}")
        flash('Erro ao registrar movimentação', 'error')
        return redirect(url_for('caixa'))

@app.route('/relatorio_caixa')
def relatorio_caixa():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    try:
        # Obter parâmetros de filtro
        tipo = request.args.get('tipo', '')
        data_inicio = request.args.get('data_inicio', '')
        data_fim = request.args.get('data_fim', '')
        
        # Obter todas as movimentações (sem limite para relatório)
        movimentacoes = listar_movimentacoes_caixa(limit=1000, tipo=tipo if tipo else None)
        
        # Calcular totais
        total_entradas = sum(m['valor'] for m in movimentacoes if m['tipo'] == 'entrada')
        total_saidas = sum(m['valor'] for m in movimentacoes if m['tipo'] == 'saida')
        saldo_total = total_entradas - total_saidas
        
        return render_template('relatorio_caixa.html',
                             movimentacoes=movimentacoes,
                             total_entradas=total_entradas,
                             total_saidas=total_saidas,
                             saldo_total=saldo_total,
                             filtro_tipo=tipo,
                             filtro_data_inicio=data_inicio,
                             filtro_data_fim=data_fim)
    
    except Exception as e:
        logger.error(f"Erro ao gerar relatório de caixa: {e}")
        flash('Erro ao gerar relatório', 'error')
        return redirect(url_for('caixa'))

@app.route('/excluir_movimentacao/<int:movimentacao_id>')
def excluir_movimentacao(movimentacao_id):
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    logger.info(f"=== INICIANDO EXCLUSÃO DE MOVIMENTAÇÃO ===")
    logger.info(f"Usuário: {session['usuario']}, Movimentação ID: {movimentacao_id}")
    
    if not usuario_tem_permissao(session['usuario'], 'caixa'):
        logger.warning(f"Usuário {session['usuario']} sem permissão para excluir movimentações")
        flash('Você não tem permissão para excluir movimentações', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        logger.info("Conectando ao banco de dados...")
        conn = get_db_connection()
        cursor = conn.cursor()
        logger.info("Conexão estabelecida com sucesso")
        
        # Buscar dados da movimentação para auditoria
        logger.info(f"Buscando dados da movimentação ID {movimentacao_id}...")
        cursor.execute('SELECT * FROM movimentacoes_caixa WHERE id = %s', (movimentacao_id,))
        movimentacao = cursor.fetchone()
        
        if not movimentacao:
            logger.warning(f"Movimentação ID {movimentacao_id} não encontrada")
            flash('Movimentação não encontrada', 'error')
            return redirect(url_for('caixa'))
        
        logger.info(f"Movimentação encontrada: Tipo={movimentacao[1]}, Valor={movimentacao[2]}, Descrição={movimentacao[3]}")
        
        # Excluir movimentação (comprovantes são excluídos automaticamente por CASCADE)
        logger.info(f"Executando DELETE da movimentação ID {movimentacao_id}...")
        cursor.execute('DELETE FROM movimentacoes_caixa WHERE id = %s', (movimentacao_id,))
        linhas_afetadas = cursor.rowcount
        logger.info(f"Linhas afetadas: {linhas_afetadas}")
        
        conn.commit()
        logger.info("Commit realizado com sucesso")
        cursor.close()
        conn.close()
        logger.info("Conexão fechada")
        
        # Registrar auditoria
        logger.info("Registrando auditoria da exclusão...")
        registrar_auditoria(
            session['usuario'], 'DELETE', 'movimentacoes_caixa', 
            movimentacao_id, str(movimentacao), None
        )
        logger.info("Auditoria registrada com sucesso")
        
        flash('Movimentação excluída com sucesso!', 'success')
        logger.info(f"✅ Movimentação ID {movimentacao_id} excluída com sucesso pelo usuário {session['usuario']}")
        return redirect(url_for('caixa'))
    
    except Exception as e:
        logger.error(f"❌ Erro ao excluir movimentação ID {movimentacao_id}: {e}")
        logger.error(f"Tipo do erro: {type(e)}")
        import traceback
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        flash('Erro ao excluir movimentação', 'error')
        return redirect(url_for('caixa'))

@app.route('/editar_movimentacao/<int:movimentacao_id>', methods=['GET', 'POST'])
def editar_movimentacao(movimentacao_id):
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    logger.info(f"🔧 === EDITAR MOVIMENTAÇÃO - INÍCIO ===")
    logger.info(f"👤 Usuário: {session['usuario']}")
    logger.info(f"🆔 Movimentação ID: {movimentacao_id}")
    logger.info(f"📋 Método HTTP: {request.method}")
    
    if not usuario_tem_permissao(session['usuario'], 'caixa'):
        logger.warning(f"⚠️ Usuário {session['usuario']} sem permissão para editar movimentações")
        flash('Você não tem permissão para editar movimentações', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        logger.info("🔌 Conectando ao banco de dados...")
        conn = get_db_connection()
        
        # IMPORTANTE: Usar RealDictCursor para retornar dados como dicionário
        import psycopg2.extras
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        logger.info("✅ Conexão estabelecida com RealDictCursor")
        
        if request.method == 'GET':
            logger.info("📖 === MÉTODO GET - CARREGANDO DADOS ===")
            
            # Buscar dados da movimentação
            logger.info(f"🔍 Buscando dados da movimentação ID {movimentacao_id}...")
            cursor.execute('SELECT * FROM movimentacoes_caixa WHERE id = %s', (movimentacao_id,))
            movimentacao = cursor.fetchone()
            
            if not movimentacao:
                logger.warning(f"❌ Movimentação ID {movimentacao_id} não encontrada")
                flash('Movimentação não encontrada', 'error')
                return redirect(url_for('caixa'))
            
            logger.info(f"✅ Movimentação encontrada:")
            logger.info(f"  🆔 ID: {movimentacao['id']}")
            logger.info(f"  📊 Tipo: '{movimentacao['tipo']}'")
            logger.info(f"  💰 Valor: R$ {movimentacao['valor']}")
            logger.info(f"  📝 Descrição: '{movimentacao['descricao']}'")
            logger.info(f"  👤 Cadastro ID: {movimentacao['cadastro_id']}")
            logger.info(f"  🏷️ Nome Pessoa: '{movimentacao['nome_pessoa']}'")
            logger.info(f"  🧾 Número Recibo: '{movimentacao['numero_recibo']}'")
            logger.info(f"  📋 Observações: '{movimentacao['observacoes']}'")
            logger.info(f"  📅 Data: {movimentacao['data_movimentacao']}")
            logger.info(f"  👨‍💼 Usuário: '{movimentacao['usuario']}'")
            
            # Buscar pessoas cadastradas
            logger.info("👥 Buscando lista de pessoas cadastradas...")
            pessoas = listar_cadastros_simples()
            logger.info(f"✅ Encontradas {len(pessoas)} pessoas cadastradas")
            
            cursor.close()
            conn.close()
            logger.info("🔌 Conexão fechada")
            
            logger.info("🎨 Renderizando template editar_movimentacao.html...")
            return render_template('editar_movimentacao.html', 
                                 movimentacao=movimentacao, 
                                 pessoas=pessoas)
        
        elif request.method == 'POST':
            logger.info("💾 === MÉTODO POST - SALVANDO ALTERAÇÕES ===")
            
            # Buscar dados atuais para auditoria
            logger.info(f"🔍 Buscando dados atuais da movimentação ID {movimentacao_id} para auditoria...")
            cursor.execute('SELECT * FROM movimentacoes_caixa WHERE id = %s', (movimentacao_id,))
            dados_anteriores = cursor.fetchone()
            
            if not dados_anteriores:
                logger.warning(f"❌ Movimentação ID {movimentacao_id} não encontrada para edição")
                flash('Movimentação não encontrada', 'error')
                return redirect(url_for('caixa'))
            
            logger.info(f"✅ Dados anteriores encontrados:")
            logger.info(f"  📊 Tipo anterior: '{dados_anteriores['tipo']}'")
            logger.info(f"  💰 Valor anterior: R$ {dados_anteriores['valor']}")
            logger.info(f"  📝 Descrição anterior: '{dados_anteriores['descricao']}'")
            
            # Processar dados do formulário
            logger.info("📋 Processando dados do formulário...")
            tipo = request.form.get('tipo')
            valor_str = request.form.get('valor', '0')
            descricao = request.form.get('descricao', '').strip()
            cadastro_id = request.form.get('cadastro_id')
            nome_pessoa = request.form.get('nome_pessoa', '').strip()
            numero_recibo = request.form.get('numero_recibo', '').strip()
            observacoes = request.form.get('observacoes', '').strip()
            
            logger.info(f"📝 Dados recebidos do formulário:")
            logger.info(f"  📊 Tipo: '{tipo}'")
            logger.info(f"  💰 Valor (string): '{valor_str}'")
            logger.info(f"  📝 Descrição: '{descricao}'")
            logger.info(f"  👤 Cadastro ID: '{cadastro_id}'")
            logger.info(f"  🏷️ Nome Pessoa: '{nome_pessoa}'")
            logger.info(f"  🧾 Número Recibo: '{numero_recibo}'")
            logger.info(f"  📋 Observações: '{observacoes}'")
            
            # Validações
            if not descricao:
                logger.warning("❌ Descrição não fornecida - validação falhou")
                flash('Descrição é obrigatória', 'error')
                return redirect(url_for('editar_movimentacao', movimentacao_id=movimentacao_id))
            
            try:
                valor = float(valor_str)
                logger.info(f"✅ Valor convertido para float: {valor}")
            except ValueError:
                logger.warning(f"❌ Erro ao converter valor '{valor_str}' para float")
                flash('Valor deve ser um número válido', 'error')
                return redirect(url_for('editar_movimentacao', movimentacao_id=movimentacao_id))
            
            if valor <= 0:
                logger.warning(f"❌ Valor inválido: {valor} - deve ser maior que zero")
                flash('Valor deve ser maior que zero', 'error')
                return redirect(url_for('editar_movimentacao', movimentacao_id=movimentacao_id))
            
            # Converter cadastro_id
            if cadastro_id == '' or cadastro_id is None:
                cadastro_id = None
                logger.info("  👤 Cadastro ID convertido para None (vazio)")
            else:
                try:
                    cadastro_id = int(cadastro_id)
                    logger.info(f"  👤 Cadastro ID convertido para int: {cadastro_id}")
                except ValueError:
                    logger.warning(f"❌ Erro ao converter cadastro_id '{cadastro_id}' para int")
                    cadastro_id = None
            
            # Atualizar movimentação
            logger.info(f"💾 Executando UPDATE da movimentação ID {movimentacao_id}...")
            cursor.execute('''
                UPDATE movimentacoes_caixa 
                SET tipo = %s, valor = %s, descricao = %s, cadastro_id = %s, 
                    nome_pessoa = %s, numero_recibo = %s, observacoes = %s
                WHERE id = %s
            ''', (tipo, valor, descricao, cadastro_id, nome_pessoa, 
                  numero_recibo, observacoes, movimentacao_id))
            
            linhas_afetadas = cursor.rowcount
            logger.info(f"📊 Linhas afetadas pelo UPDATE: {linhas_afetadas}")
            
            if linhas_afetadas == 0:
                logger.warning("❌ Nenhuma linha foi atualizada")
                flash('Erro ao atualizar movimentação', 'error')
                return redirect(url_for('editar_movimentacao', movimentacao_id=movimentacao_id))
            
            conn.commit()
            logger.info("✅ Commit realizado com sucesso")
            
            cursor.close()
            conn.close()
            logger.info("🔌 Conexão fechada")
            
            # Registrar auditoria
            logger.info("📋 Registrando auditoria da edição...")
            registrar_auditoria(
                session['usuario'], 'UPDATE', 'movimentacoes_caixa', 
                movimentacao_id, str(dados_anteriores), 
                f"Tipo: {tipo}, Valor: {valor}, Descrição: {descricao}"
            )
            logger.info("✅ Auditoria registrada com sucesso")
            
            flash('Movimentação atualizada com sucesso!', 'success')
            logger.info(f"🎉 Movimentação ID {movimentacao_id} atualizada com sucesso pelo usuário {session['usuario']}")
            return redirect(url_for('caixa'))
    
    except Exception as e:
        logger.error(f"💥 ERRO CRÍTICO ao editar movimentação ID {movimentacao_id}:")
        logger.error(f"❌ Erro: {str(e)}")
        logger.error(f"❌ Tipo do erro: {type(e).__name__}")
        import traceback
        logger.error(f"❌ Traceback completo:")
        for line in traceback.format_exc().split('\n'):
            if line.strip():
                logger.error(f"   {line}")
        
        # Tentar fechar conexões se existirem
        try:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
            logger.info("🔌 Conexões fechadas após erro")
        except:
            pass
            
        flash('Erro ao editar movimentação', 'error')
        return redirect(url_for('caixa'))

@app.route('/visualizar_comprovantes/<int:movimentacao_id>')
def visualizar_comprovantes(movimentacao_id):
    logger.info(f"🔥 ROTA VISUALIZAR_COMPROVANTES CHAMADA - ID: {movimentacao_id}")
    
    if 'usuario' not in session:
        logger.warning("❌ Usuário não logado - redirecionando para login")
        return redirect(url_for('login'))
    
    logger.info(f"📎 === VISUALIZAR COMPROVANTES - INÍCIO ===")
    logger.info(f"👤 Usuário: {session['usuario']}")
    logger.info(f"🆔 Movimentação ID: {movimentacao_id}")
    
    if not usuario_tem_permissao(session['usuario'], 'caixa'):
        logger.warning(f"⚠️ Usuário {session['usuario']} sem permissão para visualizar comprovantes")
        flash('Você não tem permissão para visualizar comprovantes', 'error')
        return redirect(url_for('dashboard'))
    
    logger.info("✅ Permissão verificada - usuário tem acesso ao caixa")
    
    try:
        logger.info("🔌 Conectando ao banco de dados...")
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        logger.info("✅ Conexão estabelecida com RealDictCursor")
        
        # Buscar dados da movimentação
        logger.info(f"🔍 Buscando dados da movimentação ID {movimentacao_id}...")
        cursor.execute('SELECT * FROM movimentacoes_caixa WHERE id = %s', (movimentacao_id,))
        movimentacao = cursor.fetchone()
        
        if not movimentacao:
            logger.warning(f"❌ Movimentação ID {movimentacao_id} não encontrada")
            flash('Movimentação não encontrada', 'error')
            return redirect(url_for('caixa'))
        
        logger.info(f"✅ Movimentação encontrada:")
        logger.info(f"  📊 Tipo: {movimentacao['tipo']}")
        logger.info(f"  💰 Valor: R$ {movimentacao['valor']}")
        logger.info(f"  📝 Descrição: {movimentacao['descricao']}")
        
        # Buscar comprovantes
        logger.info(f"📎 Chamando obter_comprovantes_movimentacao({movimentacao_id})...")
        try:
            comprovantes = obter_comprovantes_movimentacao(movimentacao_id)
            logger.info(f"✅ Comprovantes obtidos: {len(comprovantes)} arquivos")
            
            if comprovantes:
                for i, comp in enumerate(comprovantes):
                    logger.info(f"  📎 Comprovante {i+1}: {comp['nome_arquivo']} ({comp['tipo_arquivo']})")
            else:
                logger.info("  ℹ️ Nenhum comprovante encontrado")
                
        except Exception as comp_error:
            logger.error(f"❌ ERRO ao obter comprovantes: {comp_error}")
            logger.error(f"❌ Tipo do erro: {type(comp_error).__name__}")
            import traceback
            logger.error(f"❌ Traceback:")
            for line in traceback.format_exc().split('\n'):
                if line.strip():
                    logger.error(f"   {line}")
            raise comp_error
        
        cursor.close()
        conn.close()
        logger.info("🔌 Conexão fechada")
        
        logger.info("🎨 Renderizando template visualizar_comprovantes.html...")
        return render_template('visualizar_comprovantes.html', 
                             movimentacao=movimentacao, 
                             comprovantes=comprovantes)
    
    except Exception as e:
        logger.error(f"💥 ERRO CRÍTICO ao visualizar comprovantes:")
        logger.error(f"❌ Erro: {str(e)}")
        logger.error(f"❌ Tipo do erro: {type(e).__name__}")
        import traceback
        logger.error(f"❌ Traceback completo:")
        for line in traceback.format_exc().split('\n'):
            if line.strip():
                logger.error(f"   {line}")
        
        # Tentar fechar conexões se existirem
        try:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
            logger.info("🔌 Conexões fechadas após erro")
        except:
            pass
            
        flash('Erro ao carregar comprovantes', 'error')
        return redirect(url_for('caixa'))

@app.route('/download_comprovante/<int:comprovante_id>')
def download_comprovante(comprovante_id):
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    if not usuario_tem_permissao(session['usuario'], 'caixa'):
        flash('Você não tem permissão para baixar comprovantes', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT nome_arquivo, tipo_arquivo, arquivo_dados
            FROM comprovantes_caixa
            WHERE id = %s
        ''', (comprovante_id,))
        
        comprovante = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not comprovante:
            flash('Comprovante não encontrado', 'error')
            return redirect(url_for('caixa'))
        
        import io
        return send_file(
            io.BytesIO(comprovante[2]),
            as_attachment=True,
            download_name=comprovante[0],
            mimetype=comprovante[1]
        )
    
    except Exception as e:
        logger.error(f"Erro ao baixar comprovante: {e}")
        flash('Erro ao baixar comprovante', 'error')
        return redirect(url_for('caixa'))

@app.route('/exportar_comprovantes_pdf/<int:movimentacao_id>')
def exportar_comprovantes_pdf(movimentacao_id):
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    if not usuario_tem_permissao(session['usuario'], 'caixa'):
        flash('Você não tem permissão para exportar comprovantes', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        import io
        from PIL import Image as PILImage
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Buscar dados da movimentação
        cursor.execute('SELECT * FROM movimentacoes_caixa WHERE id = %s', (movimentacao_id,))
        movimentacao = cursor.fetchone()
        
        if not movimentacao:
            flash('Movimentação não encontrada', 'error')
            return redirect(url_for('caixa'))
        
        # Buscar comprovantes
        comprovantes = obter_comprovantes_movimentacao(movimentacao_id)
        
        cursor.close()
        conn.close()
        
        # Criar PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []
        
        # Título
        title = Paragraph(f"AMEG - Comprovantes da Movimentação #{movimentacao_id}", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 20))
        
        # Dados da movimentação
        mov_data = [
            ['Tipo:', movimentacao['tipo'].title()],
            ['Valor:', f"R$ {movimentacao['valor']:.2f}"],
            ['Descrição:', movimentacao['descricao']],
            ['Data:', movimentacao['data_movimentacao'].strftime('%d/%m/%Y %H:%M')],
            ['Usuário:', movimentacao['usuario']]
        ]
        
        mov_table = Table(mov_data, colWidths=[2*inch, 4*inch])
        mov_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(mov_table)
        elements.append(Spacer(1, 30))
        
        # Incluir os comprovantes reais
        if comprovantes:
            elements.append(Paragraph("Comprovantes Anexados:", styles['Heading2']))
            elements.append(Spacer(1, 20))
            
            for i, comp in enumerate(comprovantes, 1):
                # Título do comprovante
                elements.append(Paragraph(f"{i}. {comp['nome_arquivo']}", styles['Heading3']))
                elements.append(Spacer(1, 10))
                
                # Buscar dados do arquivo
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('SELECT arquivo_dados FROM comprovantes_caixa WHERE id = %s', (comp['id'],))
                arquivo_dados = cursor.fetchone()[0]
                cursor.close()
                conn.close()
                
                try:
                    if comp['tipo_arquivo'].startswith('image/'):
                        # Para imagens, incluir no PDF
                        img_buffer = io.BytesIO(arquivo_dados)
                        pil_img = PILImage.open(img_buffer)
                        
                        # Redimensionar se necessário
                        max_width, max_height = 400, 300
                        pil_img.thumbnail((max_width, max_height), PILImage.Resampling.LANCZOS)
                        
                        # Converter para ReportLab
                        img_buffer2 = io.BytesIO()
                        pil_img.save(img_buffer2, format='PNG')
                        img_buffer2.seek(0)
                        
                        img = Image(img_buffer2, width=pil_img.width, height=pil_img.height)
                        elements.append(img)
                        
                    elif comp['tipo_arquivo'] == 'application/pdf':
                        # Para PDFs, adicionar nota
                        elements.append(Paragraph(f"📄 Arquivo PDF: {comp['nome_arquivo']}", styles['Normal']))
                        elements.append(Paragraph("(Conteúdo do PDF não pode ser incorporado)", styles['Italic']))
                        
                    else:
                        # Para outros tipos, adicionar informação
                        elements.append(Paragraph(f"📎 Arquivo: {comp['nome_arquivo']}", styles['Normal']))
                        elements.append(Paragraph(f"Tipo: {comp['tipo_arquivo']}", styles['Normal']))
                        
                except Exception as file_error:
                    logger.error(f"Erro ao processar arquivo {comp['nome_arquivo']}: {file_error}")
                    elements.append(Paragraph(f"❌ Erro ao processar arquivo: {comp['nome_arquivo']}", styles['Normal']))
                
                elements.append(Spacer(1, 20))
        else:
            elements.append(Paragraph("Nenhum comprovante anexado.", styles['Normal']))
        
        doc.build(elements)
        buffer.seek(0)
        
        filename = f"comprovantes_movimentacao_{movimentacao_id}.pdf"
        return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')
    
    except Exception as e:
        logger.error(f"Erro ao exportar comprovantes PDF: {e}")
        flash('Erro ao gerar PDF dos comprovantes', 'error')
        return redirect(url_for('caixa'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🚀 Iniciando AMEG na porta {port}")
    logger.info(f"Debug mode: {app.debug}")
    logger.info(f"Environment: {'Railway' if os.environ.get('RAILWAY_ENVIRONMENT') else 'Local'}")
    app.run(host='0.0.0.0', port=port, debug=False)
@app.route('/auditoria')
def auditoria():
    logger.info("🔍 Acessando rota de auditoria")
    
    if 'usuario' not in session:
        logger.debug("Usuário não logado tentando acessar auditoria")
        return redirect(url_for('login'))
    
    # Verificar se é admin
    if session.get('tipo') != 'admin':
        logger.warning(f"Usuário {session.get('usuario')} (tipo: {session.get('tipo')}) tentou acessar auditoria")
        flash('Acesso negado. Apenas administradores podem acessar a auditoria.')
        return redirect(url_for('dashboard'))
    
    logger.info(f"Admin {session.get('usuario')} acessando auditoria")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        logger.debug("Conexão estabelecida para auditoria")
        
        # Parâmetros de filtro
        usuario_filtro = request.args.get('usuario', '')
        acao_filtro = request.args.get('acao', '')
        tabela_filtro = request.args.get('tabela', '')
        data_inicial = request.args.get('data_inicial', '')
        data_final = request.args.get('data_final', '')
        page = int(request.args.get('page', 1))
        per_page = 50
        
        logger.debug(f"Filtros: usuario={usuario_filtro}, acao={acao_filtro}, tabela={tabela_filtro}")
        
        # Construir query com filtros
        where_conditions = []
        params = []
        
        if usuario_filtro:
            where_conditions.append("usuario ILIKE %s")
            params.append(f"%{usuario_filtro}%")
        
        if acao_filtro:
            where_conditions.append("acao = %s")
            params.append(acao_filtro)
        
        if tabela_filtro:
            where_conditions.append("tabela = %s")
            params.append(tabela_filtro)
        
        if data_inicial:
            where_conditions.append("DATE(data_acao) >= %s")
            params.append(data_inicial)
        
        if data_final:
            where_conditions.append("DATE(data_acao) <= %s")
            params.append(data_final)
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        logger.debug(f"WHERE clause: {where_clause}")
        
        # Contar total de registros
        cursor.execute(f"SELECT COUNT(*) as total FROM auditoria {where_clause}", params)
        total_records = cursor.fetchone()['total']
        total_pages = (total_records + per_page - 1) // per_page
        
        logger.debug(f"Total de registros: {total_records}")
        
        # Buscar registros com paginação
        offset = (page - 1) * per_page
        cursor.execute(f"""
            SELECT * FROM auditoria {where_clause}
            ORDER BY data_acao DESC
            LIMIT %s OFFSET %s
        """, params + [per_page, offset])
        
        auditorias = cursor.fetchall()
        logger.debug(f"Registros encontrados: {len(auditorias)}")
        
        # Estatísticas
        cursor.execute("SELECT COUNT(*) as total FROM auditoria")
        stats_total = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as hoje FROM auditoria WHERE DATE(data_acao) = CURRENT_DATE")
        stats_hoje = cursor.fetchone()['hoje']
        
        cursor.execute("SELECT COUNT(DISTINCT usuario) as usuarios FROM auditoria WHERE DATE(data_acao) >= CURRENT_DATE - INTERVAL '7 days'")
        stats_usuarios = cursor.fetchone()['usuarios']
        
        cursor.execute("SELECT data_acao FROM auditoria ORDER BY data_acao DESC LIMIT 1")
        ultima_acao = cursor.fetchone()
        stats_ultima = ultima_acao['data_acao'].strftime('%H:%M') if ultima_acao else 'N/A'
        
        stats = {
            'total': stats_total,
            'hoje': stats_hoje,
            'usuarios_ativos': stats_usuarios,
            'ultima_acao': stats_ultima
        }
        
        logger.debug(f"Estatísticas: {stats}")
        
        # Parâmetros para paginação
        query_params = "&".join([f"{k}={v}" for k, v in request.args.items() if k != 'page'])
        
        cursor.close()
        conn.close()
        
        logger.info("✅ Dados de auditoria carregados com sucesso")
        
        return render_template('auditoria.html', 
                             auditorias=auditorias,
                             stats=stats,
                             page=page,
                             total_pages=total_pages,
                             query_params=query_params)
        
    except Exception as e:
        logger.error(f"❌ Erro ao carregar auditoria: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        flash('Erro ao carregar dados de auditoria.')
        return redirect(url_for('dashboard'))
@app.route('/admin/reset')
def admin_reset():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    # Verificar se é o admin ID 1
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM usuarios WHERE usuario = %s AND id = 1', (session['usuario'],))
    admin_check = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not admin_check:
        flash('Acesso negado! Apenas o admin principal pode acessar esta funcionalidade.')
        return redirect(url_for('dashboard'))
    
    return render_template('admin_reset.html')

@app.route('/admin/reset/execute', methods=['POST'])
def admin_reset_execute():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    # Verificar se é o admin ID 1
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM usuarios WHERE usuario = %s AND id = 1', (session['usuario'],))
    admin_check = cursor.fetchone()
    
    if not admin_check:
        cursor.close()
        conn.close()
        flash('Acesso negado! Apenas o admin principal pode executar o reset.')
        return redirect(url_for('dashboard'))
    
    try:
        logger.warning(f"🚨 RESET INICIADO pelo admin ID 1: {session['usuario']}")
        
        # Zerar tabelas (mantém estrutura)
        cursor.execute('TRUNCATE TABLE arquivos_saude RESTART IDENTITY CASCADE')
        cursor.execute('TRUNCATE TABLE auditoria RESTART IDENTITY CASCADE')
        cursor.execute('TRUNCATE TABLE cadastros RESTART IDENTITY CASCADE')
        
        # Resetar sequences manualmente (garantia)
        cursor.execute('ALTER SEQUENCE arquivos_saude_id_seq RESTART WITH 1')
        cursor.execute('ALTER SEQUENCE auditoria_id_seq RESTART WITH 1')
        cursor.execute('ALTER SEQUENCE cadastros_id_seq RESTART WITH 1')
        
        conn.commit()
        
        # Registrar auditoria do reset
        registrar_auditoria(
            usuario=session['usuario'],
            acao='RESET',
            tabela='SISTEMA',
            dados_novos='Reset completo das tabelas: cadastros, arquivos_saude, auditoria',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        logger.warning(f"✅ RESET CONCLUÍDO pelo admin ID 1: {session['usuario']}")
        flash('Reset executado com sucesso! Todas as tabelas foram zeradas e contadores reiniciados.')
        
    except Exception as e:
        logger.error(f"❌ Erro durante reset: {e}")
        flash(f'Erro durante reset: {str(e)}')
        conn.rollback()
    
    cursor.close()
    conn.close()
    return redirect(url_for('admin_reset'))
@app.route('/api/stats')
def api_stats():
    if 'usuario' not in session:
        return {"error": "Não autorizado"}, 401
    
    try:
        # Usar cache para estatísticas
        stats = get_cached_stats()
        
        return {
            "cadastros": stats['total'],
            "arquivos": stats['arquivos'],
            "auditoria": stats.get('auditoria', 0)  # Fallback para compatibilidade
        }
        
    except Exception as e:
        logger.error(f"Erro na API stats: {e}")
        return {"error": str(e)}, 500
