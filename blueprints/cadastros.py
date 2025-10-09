from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import get_db_connection, registrar_auditoria
from werkzeug.utils import secure_filename
import psycopg2.extras
import logging
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)

cadastros_bp = Blueprint('cadastros', __name__)

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

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}

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

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@cadastros_bp.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    if 'usuario' not in session:
        logger.debug("Usuário não logado tentando acessar /cadastrar")
        return redirect(url_for('auth.login'))
    
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
            from blueprints.dashboard import invalidate_stats_cache
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
            return redirect(url_for('dashboard.dashboard'))
        
        except Exception as e:
            logger.error(f"❌ Erro ao salvar cadastro: {e}")
            logger.error(f"Tipo do erro: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            flash('Erro ao salvar cadastro. Tente novamente.')
            return redirect(url_for('cadastros.cadastrar'))
    
    return render_template('cadastrar.html')

@cadastros_bp.route('/editar_cadastro/<int:cadastro_id>')
def editar_cadastro(cadastro_id):
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute('SELECT *, foto_base64 FROM cadastros WHERE id = %s', (cadastro_id))
        cadastro = cursor.fetchone()
        
        arquivos_saude = []
        dados_saude_pessoas = []
        if cadastro:
            cursor.execute('SELECT id, nome_arquivo, tipo_arquivo, descricao, data_upload FROM arquivos_saude WHERE cadastro_id = %s ORDER BY data_upload DESC', (cadastro_id))
            arquivos_saude = cursor.fetchall()
            
            cursor.execute('SELECT * FROM dados_saude_pessoa WHERE cadastro_id = %s ORDER BY id', (cadastro_id))
            dados_saude_pessoas = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        if not cadastro:
            flash('Cadastro não encontrado!')
            return redirect(url_for('dashboard.dashboard'))
        
        return render_template('editar_cadastro.html', cadastro=cadastro, arquivos_saude=arquivos_saude, dados_saude_pessoas=dados_saude_pessoas)
        
    except Exception as e:
        logger.error(f"Erro ao carregar cadastro: {e}")
        flash('Erro ao carregar cadastro.')
        return redirect(url_for('dashboard.dashboard'))

@cadastros_bp.route('/atualizar_cadastro/<int:cadastro_id>', methods=['POST'])
def atualizar_cadastro(cadastro_id):
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    validation_errors = validate_field_lengths(request.form)
    if validation_errors:
        for error in validation_errors:
            flash(f"Erro de validação: {error}", 'error')
        return redirect(url_for('cadastros.editar_cadastro', cadastro_id=cadastro_id))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
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
        
        campos_int = ['idade', 'idade_companheiro', 'pessoas_trabalham', 'aposentados_pensionistas', 
                     'num_pessoas_familia', 'num_familias', 'adultos', 'criancas', 'adolescentes', 
                     'idosos', 'gestantes', 'nutrizes', 'dias_semana_trabalha', 'pessoas_dependem_renda']
        
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
        
        set_clauses = [f"{campo} = %s" for campo in campos]
        sql_update = f"UPDATE cadastros SET {', '.join(set_clauses)} WHERE id = %s"
        
        cursor.execute(sql_update, valores)
        
        rows_affected = cursor.rowcount
        
        if rows_affected > 0:
            # Upload de novos arquivos
            uploaded_files = []
            for file_type in ['laudo', 'receita', 'imagem']:
                files = request.files.getlist(f'{file_type}[]')
                descriptions = request.form.getlist(f'descricao_{file_type}[]')
                
                for i, file in enumerate(files):
                    if file and file.filename and allowed_file(file.filename):
                        file_data = file.read()
                        descricao = descriptions[i] if i < len(descriptions) else ''
                        
                        cursor.execute('INSERT INTO arquivos_saude (cadastro_id, nome_arquivo, tipo_arquivo, arquivo_dados, descricao) VALUES (%s, %s, %s, %s, %s)', 
                                    (cadastro_id, file.filename, file_type, file_data, descricao))
                        
                        uploaded_files.append(f"{file_type}: {file.filename}")
            
            # Processar dados de saúde por pessoa
            cursor.execute('DELETE FROM dados_saude_pessoa WHERE cadastro_id = %s', (cadastro_id))
            
            pessoas_saude = []
            for key in request.form.keys():
                if key.startswith('saude_nome_'):
                    pessoa_num = key.split('_')[-1]
                    nome_pessoa = request.form.get(f'saude_nome_{pessoa_num}')
                    
                    if nome_pessoa:
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
            
            conn.commit()
            
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
            flash('Nenhuma alteração foi feita no cadastro.')
        
    except Exception as e:
        logger.error(f"Erro ao atualizar cadastro: {e}")
        flash('Erro interno do sistema. Tente novamente.')
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
    
    return redirect(url_for('dashboard.dashboard'))

@cadastros_bp.route('/deletar_cadastro/<int:cadastro_id>', methods=['POST'])
def deletar_cadastro(cadastro_id):
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Deletar arquivos de saúde relacionados primeiro
        cursor.execute('DELETE FROM arquivos_saude WHERE cadastro_id = %s', (cadastro_id))
        
        # Deletar o cadastro
        cursor.execute('DELETE FROM cadastros WHERE id = %s', (cadastro_id))
        cadastros_deletados = cursor.rowcount
        
        if cadastros_deletados > 0:
            conn.commit()
            flash('Cadastro deletado com sucesso!')
        else:
            flash('Cadastro não encontrado!')
            
    except Exception as e:
        logger.error(f"Erro ao deletar cadastro: {e}")
        flash(f'Erro ao deletar cadastro: {str(e)}')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('dashboard.dashboard'))
