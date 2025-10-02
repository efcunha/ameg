from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, send_from_directory
from database import get_db_connection, init_db_tables, create_admin_user
from db_helper import get_db, execute_query
import csv
import io
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'ameg_secret_2024_fallback_key_change_in_production')
app.config['UPLOAD_FOLDER'] = 'uploads/saude'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Inicializar banco na inicialização (apenas no Railway)
if os.environ.get('RAILWAY_ENVIRONMENT'):
    try:
        init_db_tables()
        create_admin_user()
        print("✅ Banco inicializado no Railway")
    except Exception as e:
        print(f"Erro na inicialização do banco: {e}")

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}

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
    
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    
    if db_type == 'postgresql':
        cursor.execute('SELECT senha FROM usuarios WHERE usuario = %s', (usuario,))
    else:
        cursor.execute('SELECT senha FROM usuarios WHERE usuario = ?', (usuario,))
    
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
    
    conn, db_type = get_db_connection()
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
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        conn, db_type = get_db()
        cursor = conn.cursor()
        
        from db_helper import execute_query
        
        execute_query("""INSERT INTO cadastros (
            nome_completo, endereco, numero, bairro, cep, telefone, ponto_referencia, genero, idade,
            data_nascimento, titulo_eleitor, cidade_titulo, cpf, rg, nis, estado_civil,
            escolaridade, profissao, nome_companheiro, cpf_companheiro, rg_companheiro,
            idade_companheiro, escolaridade_companheiro, profissao_companheiro, data_nascimento_companheiro,
            titulo_companheiro, cidade_titulo_companheiro, nis_companheiro, tipo_trabalho,
            pessoas_trabalham, aposentados_pensionistas, num_pessoas_familia, num_familias,
            adultos, criancas, adolescentes, idosos, gestantes, nutrizes, renda_familiar,
            renda_per_capita, bolsa_familia, casa_tipo, casa_material, energia, lixo, agua,
            esgoto, observacoes, tem_doenca_cronica, doencas_cronicas, usa_medicamento_continuo,
            medicamentos_continuos, tem_doenca_mental, doencas_mentais, tem_deficiencia,
            tipo_deficiencia, precisa_cuidados_especiais, cuidados_especiais
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (request.form.get('nome_completo'), request.form.get('endereco'), request.form.get('numero'),
         request.form.get('bairro'), request.form.get('cep'), request.form.get('telefone'),
         request.form.get('ponto_referencia'), request.form.get('genero'), request.form.get('idade'),
         request.form.get('data_nascimento'), request.form.get('titulo_eleitor'), request.form.get('cidade_titulo'),
         request.form.get('cpf'), request.form.get('rg'), request.form.get('nis'),
         request.form.get('estado_civil'), request.form.get('escolaridade'), request.form.get('profissao'),
         request.form.get('nome_companheiro'), request.form.get('cpf_companheiro'), request.form.get('rg_companheiro'),
         request.form.get('idade_companheiro'), request.form.get('escolaridade_companheiro'), request.form.get('profissao_companheiro'),
         request.form.get('data_nascimento_companheiro'), request.form.get('titulo_companheiro'), request.form.get('cidade_titulo_companheiro'),
         request.form.get('nis_companheiro'), request.form.get('tipo_trabalho'), request.form.get('pessoas_trabalham'),
         request.form.get('aposentados_pensionistas'), request.form.get('num_pessoas_familia'), request.form.get('num_familias'),
         request.form.get('adultos'), request.form.get('criancas'), request.form.get('adolescentes'),
         request.form.get('idosos'), request.form.get('gestantes'), request.form.get('nutrizes'),
         request.form.get('renda_familiar'), request.form.get('renda_per_capita'), request.form.get('bolsa_familia'),
         request.form.get('casa_tipo'), request.form.get('casa_material'), request.form.get('energia'),
         request.form.get('lixo'), request.form.get('agua'), request.form.get('esgoto'),
         request.form.get('observacoes'), request.form.get('tem_doenca_cronica'), request.form.get('doencas_cronicas'),
         request.form.get('usa_medicamento_continuo'), request.form.get('medicamentos_continuos'), request.form.get('tem_doenca_mental'),
         request.form.get('doencas_mentais'), request.form.get('tem_deficiencia'), request.form.get('tipo_deficiencia'),
         request.form.get('precisa_cuidados_especiais'), request.form.get('cuidados_especiais')))
        
        # Para obter o ID do cadastro inserido, fazer uma query separada
        conn, db_type = get_db()
        cursor = conn.cursor()
        
        if db_type == 'postgresql':
            cursor.execute('SELECT id FROM cadastros ORDER BY id DESC LIMIT 1')
        else:
            cursor.execute('SELECT last_insert_rowid()')
        
        result = cursor.fetchone()
        if result:
            cadastro_id = result[0]
        else:
            cadastro_id = None
        
        # Upload de arquivos
        uploaded_files = []
        if cadastro_id:
            for file_key in ['laudo', 'receita', 'imagem']:
                if file_key in request.files:
                file = request.files[file_key]
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(f"{cadastro_id}_{file_key}_{file.filename}")
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    
                    descricao = request.form.get(f'descricao_{file_key}', '')
                    cursor.execute('INSERT INTO arquivos_saude (cadastro_id, nome_arquivo, tipo_arquivo, caminho_arquivo, descricao) VALUES (?, %s, %s, %s, %s)', 
                             (cadastro_id, file.filename, file_key, filepath, descricao))
                    uploaded_files.append(file_key)
        
        conn.commit()
        conn.close()
        
        if uploaded_files:
            flash(f'Cadastro realizado com sucesso! Arquivos enviados: {", ".join(uploaded_files)}')
        else:
            flash('Cadastro realizado com sucesso!')
        return redirect(url_for('dashboard'))
    
    return render_template('cadastrar.html')

@app.route('/relatorios')
def relatorios():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('tipos_relatorios.html')

@app.route('/relatorio_saude')
def relatorio_saude():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    c = cursor = conn[0].cursor() if isinstance(conn, tuple) else conn.cursor()
    
    c.execute('SELECT COUNT(*) FROM cadastros WHERE tem_doenca_cronica = "Sim"')
    com_doenca_cronica = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM cadastros WHERE usa_medicamento_continuo = "Sim"')
    usa_medicamento = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM cadastros WHERE tem_doenca_mental = "Sim"')
    com_doenca_mental = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM cadastros WHERE tem_deficiencia = "Sim"')
    com_deficiencia = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM cadastros WHERE precisa_cuidados_especiais = "Sim"')
    precisa_cuidados = c.fetchone()[0]
    
    c.execute("""SELECT id, nome_completo, idade, telefone, bairro, tem_doenca_cronica, doencas_cronicas,
                 usa_medicamento_continuo, medicamentos_continuos, tem_doenca_mental, doencas_mentais,
                 tem_deficiencia, tipo_deficiencia, precisa_cuidados_especiais, cuidados_especiais
                 FROM cadastros 
                 WHERE tem_doenca_cronica = "Sim" OR usa_medicamento_continuo = "Sim" 
                 OR tem_doenca_mental = "Sim" OR tem_deficiencia = "Sim" 
                 OR precisa_cuidados_especiais = "Sim"
                 ORDER BY nome_completo""")
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
        filename = secure_filename(f"{cadastro_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        conn = get_db_connection()
        c = cursor = conn[0].cursor() if isinstance(conn, tuple) else conn.cursor()
        c.execute('INSERT INTO arquivos_saude (cadastro_id, nome_arquivo, tipo_arquivo, caminho_arquivo, descricao) VALUES (?, %s, %s, %s, %s)', 
                 (cadastro_id, file.filename, request.form.get('tipo_arquivo'), filepath, request.form.get('descricao')))
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
    return render_template('usuarios.html')

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
    
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    
    try:
        senha_hash = generate_password_hash(nova_senha)
        if db_type == 'postgresql':
            cursor.execute('INSERT INTO usuarios (usuario, senha) VALUES (%s, %s)', (novo_usuario, senha_hash))
        else:
            cursor.execute('INSERT INTO usuarios (usuario, senha) VALUES (?, ?)', (novo_usuario, senha_hash))
        
        conn.commit()
        flash('Usuário criado com sucesso!')
    except Exception as e:
        flash(f'Erro ao criar usuário: {str(e)}')
    
    cursor.close()
    conn.close()
    return redirect(url_for('usuarios'))

@app.route('/editar_cadastro/<int:cadastro_id>')
def editar_cadastro(cadastro_id):
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    conn, db_type = get_db()
    cursor = conn.cursor()
    
    print(f"DEBUG: Buscando cadastro ID {cadastro_id}")
    
    if db_type == 'postgresql':
        cursor.execute('SELECT * FROM cadastros WHERE id = %s', (cadastro_id,))
    else:
        cursor.execute('SELECT * FROM cadastros WHERE id = ?', (cadastro_id,))
    
    cadastro = cursor.fetchone()
    print(f"DEBUG: Cadastro encontrado: {cadastro is not None}")
    if cadastro:
        print(f"DEBUG: Dados do cadastro: {dict(cadastro) if hasattr(cadastro, 'keys') else 'Dados existem'}")
    
    cursor.close()
    conn.close()
    
    if not cadastro:
        flash('Cadastro não encontrado!')
        return redirect(url_for('dashboard'))
    
    return render_template('editar_cadastro.html', cadastro=cadastro)

@app.route('/atualizar_cadastro/<int:cadastro_id>', methods=['POST'])
def atualizar_cadastro(cadastro_id):
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    conn, db_type = get_db()
    cursor = conn.cursor()
    
    # Campos do formulário
    campos = [
        'nome_completo', 'endereco', 'numero', 'bairro', 'cep', 'telefone', 'ponto_referencia',
        'genero', 'idade', 'data_nascimento', 'titulo_eleitor', 'cidade_titulo',
        'cpf', 'rg', 'nis', 'estado_civil', 'escolaridade', 'profissao',
        'nome_companheiro', 'cpf_companheiro', 'rg_companheiro', 'idade_companheiro',
        'escolaridade_companheiro', 'profissao_companheiro', 'qtd_filhos',
        'nomes_idades_filhos', 'renda_familiar', 'beneficio_governo',
        'qual_beneficio', 'casa_propria', 'tipo_casa', 'qtd_comodos',
        'energia_eletrica', 'agua_encanada', 'rede_esgoto', 'coleta_lixo',
        'doencas_familia', 'medicamentos_uso', 'deficiencia_familia',
        'tipo_deficiencia', 'acompanhamento_medico', 'local_atendimento'
    ]
    
    valores = [request.form.get(campo, '') for campo in campos]
    valores.append(cadastro_id)
    
    sql_update = f"""
    UPDATE cadastros SET 
    nome_completo = {'%s' if db_type == 'postgresql' else '?'},
    endereco = {'%s' if db_type == 'postgresql' else '?'},
    numero = {'%s' if db_type == 'postgresql' else '?'},
    bairro = {'%s' if db_type == 'postgresql' else '?'},
    cep = {'%s' if db_type == 'postgresql' else '?'},
    telefone = {'%s' if db_type == 'postgresql' else '?'},
    ponto_referencia = {'%s' if db_type == 'postgresql' else '?'},
    genero = {'%s' if db_type == 'postgresql' else '?'},
    idade = {'%s' if db_type == 'postgresql' else '?'},
    data_nascimento = {'%s' if db_type == 'postgresql' else '?'},
    titulo_eleitor = {'%s' if db_type == 'postgresql' else '?'},
    cidade_titulo = {'%s' if db_type == 'postgresql' else '?'},
    cpf = {'%s' if db_type == 'postgresql' else '?'},
    rg = {'%s' if db_type == 'postgresql' else '?'},
    nis = {'%s' if db_type == 'postgresql' else '?'},
    estado_civil = {'%s' if db_type == 'postgresql' else '?'},
    escolaridade = {'%s' if db_type == 'postgresql' else '?'},
    profissao = {'%s' if db_type == 'postgresql' else '?'},
    nome_companheiro = {'%s' if db_type == 'postgresql' else '?'},
    cpf_companheiro = {'%s' if db_type == 'postgresql' else '?'},
    rg_companheiro = {'%s' if db_type == 'postgresql' else '?'},
    idade_companheiro = {'%s' if db_type == 'postgresql' else '?'},
    escolaridade_companheiro = {'%s' if db_type == 'postgresql' else '?'},
    profissao_companheiro = {'%s' if db_type == 'postgresql' else '?'},
    qtd_filhos = {'%s' if db_type == 'postgresql' else '?'},
    nomes_idades_filhos = {'%s' if db_type == 'postgresql' else '?'},
    renda_familiar = {'%s' if db_type == 'postgresql' else '?'},
    beneficio_governo = {'%s' if db_type == 'postgresql' else '?'},
    qual_beneficio = {'%s' if db_type == 'postgresql' else '?'},
    casa_propria = {'%s' if db_type == 'postgresql' else '?'},
    tipo_casa = {'%s' if db_type == 'postgresql' else '?'},
    qtd_comodos = {'%s' if db_type == 'postgresql' else '?'},
    energia_eletrica = {'%s' if db_type == 'postgresql' else '?'},
    agua_encanada = {'%s' if db_type == 'postgresql' else '?'},
    rede_esgoto = {'%s' if db_type == 'postgresql' else '?'},
    coleta_lixo = {'%s' if db_type == 'postgresql' else '?'},
    doencas_familia = {'%s' if db_type == 'postgresql' else '?'},
    medicamentos_uso = {'%s' if db_type == 'postgresql' else '?'},
    deficiencia_familia = {'%s' if db_type == 'postgresql' else '?'},
    tipo_deficiencia = {'%s' if db_type == 'postgresql' else '?'},
    acompanhamento_medico = {'%s' if db_type == 'postgresql' else '?'},
    local_atendimento = {'%s' if db_type == 'postgresql' else '?'}
    WHERE id = {'%s' if db_type == 'postgresql' else '?'}
    """
    
    try:
        cursor.execute(sql_update, valores)
        conn.commit()
        flash('Cadastro atualizado com sucesso!')
    except Exception as e:
        flash(f'Erro ao atualizar cadastro: {str(e)}')
    
    cursor.close()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/deletar_cadastro/<int:cadastro_id>', methods=['POST'])
def deletar_cadastro(cadastro_id):
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    conn, db_type = get_db()
    cursor = conn.cursor()
    
    try:
        # Deletar arquivos de saúde relacionados
        if db_type == 'postgresql':
            cursor.execute('DELETE FROM arquivos_saude WHERE cadastro_id = %s', (cadastro_id,))
            cursor.execute('DELETE FROM cadastros WHERE id = %s', (cadastro_id,))
        else:
            cursor.execute('DELETE FROM arquivos_saude WHERE cadastro_id = ?', (cadastro_id,))
            cursor.execute('DELETE FROM cadastros WHERE id = ?', (cadastro_id,))
        
        conn.commit()
        flash('Cadastro deletado com sucesso!')
    except Exception as e:
        flash(f'Erro ao deletar cadastro: {str(e)}')
    
    cursor.close()
    conn.close()
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Iniciando AMEG na porta {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
