from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, send_from_directory
from database import get_db_connection, init_db_tables, create_admin_user
from db_helper import get_db, execute_query
import csv
import io
import os
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuração baseada no ambiente
if os.environ.get('RAILWAY_ENVIRONMENT'):
    from config import RailwayConfig
    app.config.from_object(RailwayConfig)
elif os.environ.get('FLASK_ENV') == 'production':
    from config import ProductionConfig
    app.config.from_object(ProductionConfig)
else:
    from config import DevelopmentConfig
    app.config.from_object(DevelopmentConfig)

# Fallback para desenvolvimento
if not app.config.get('SECRET_KEY'):
    app.config['SECRET_KEY'] = 'ameg_secret_2024'
if not app.config.get('UPLOAD_FOLDER'):
    app.config['UPLOAD_FOLDER'] = 'uploads/saude'
if not app.config.get('MAX_CONTENT_LENGTH'):
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def login():
    if 'usuario' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def fazer_login():
    usuario = request.form['usuario']
    senha = request.form['senha']
    
    users = execute_query('SELECT senha FROM usuarios WHERE usuario = ?', (usuario,), fetch=True)
    
    if users and check_password_hash(users[0]['senha'], senha):
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
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM cadastros')
    total = c.fetchone()[0]
    
    c.execute('SELECT id, nome_completo, telefone, bairro, data_cadastro FROM cadastros ORDER BY data_cadastro DESC LIMIT 5')
    ultimos = c.fetchall()
    conn.close()
    
    return render_template('dashboard.html', total=total, ultimos=ultimos)

@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute("""INSERT INTO cadastros (
            nome_completo, endereco, bairro, telefone, ponto_referencia, genero, idade,
            titulo_eleitor, cidade_titulo, cpf, data_nascimento, rg, estado_civil,
            nis, escolaridade, profissao, nome_companheiro, cpf_companheiro, rg_companheiro,
            titulo_companheiro, cidade_titulo_companheiro, nis_companheiro, idade_companheiro,
            escolaridade_companheiro, profissao_companheiro, data_nascimento_companheiro,
            tipo_trabalho, pessoas_trabalham, aposentados_pensionistas, num_pessoas_familia,
            num_familias, adultos, criancas, adolescentes, idosos, gestantes, nutrizes,
            renda_familiar, renda_per_capita, bolsa_familia, casa_tipo, casa_material,
            energia, lixo, agua, esgoto, observacoes, tem_doenca_cronica, doencas_cronicas,
            usa_medicamento_continuo, medicamentos_continuos, tem_doenca_mental, doencas_mentais,
            tem_deficiencia, tipo_deficiencia, precisa_cuidados_especiais, cuidados_especiais
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (request.form.get('nome_completo'), request.form.get('endereco'),
         request.form.get('bairro'), request.form.get('telefone'),
         request.form.get('ponto_referencia'), request.form.get('genero'),
         request.form.get('idade'), request.form.get('titulo_eleitor'),
         request.form.get('cidade_titulo'), request.form.get('cpf'),
         request.form.get('data_nascimento'), request.form.get('rg'),
         request.form.get('estado_civil'), request.form.get('nis'),
         request.form.get('escolaridade'), request.form.get('profissao'),
         request.form.get('nome_companheiro'), request.form.get('cpf_companheiro'),
         request.form.get('rg_companheiro'), request.form.get('titulo_companheiro'),
         request.form.get('cidade_titulo_companheiro'), request.form.get('nis_companheiro'),
         request.form.get('idade_companheiro'), request.form.get('escolaridade_companheiro'),
         request.form.get('profissao_companheiro'), request.form.get('data_nascimento_companheiro'),
         request.form.get('tipo_trabalho'), request.form.get('pessoas_trabalham'),
         request.form.get('aposentados_pensionistas'), request.form.get('num_pessoas_familia'),
         request.form.get('num_familias'), request.form.get('adultos'),
         request.form.get('criancas'), request.form.get('adolescentes'),
         request.form.get('idosos'), request.form.get('gestantes'),
         request.form.get('nutrizes'), request.form.get('renda_familiar'),
         request.form.get('renda_per_capita'), request.form.get('bolsa_familia'),
         request.form.get('casa_tipo'), request.form.get('casa_material'),
         request.form.get('energia'), request.form.get('lixo'),
         request.form.get('agua'), request.form.get('esgoto'),
         request.form.get('observacoes'), request.form.get('tem_doenca_cronica'),
         request.form.get('doencas_cronicas'), request.form.get('usa_medicamento_continuo'),
         request.form.get('medicamentos_continuos'), request.form.get('tem_doenca_mental'),
         request.form.get('doencas_mentais'), request.form.get('tem_deficiencia'),
         request.form.get('tipo_deficiencia'), request.form.get('precisa_cuidados_especiais'),
         request.form.get('cuidados_especiais')))
        
        conn.commit()
        cadastro_id = c.lastrowid
        
        # Upload de arquivos
        uploaded_files = []
        for file_key in ['laudo', 'receita', 'imagem']:
            if file_key in request.files:
                file = request.files[file_key]
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(f"{cadastro_id}_{file_key}_{file.filename}")
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    
                    descricao = request.form.get(f'descricao_{file_key}', '')
                    c.execute('INSERT INTO arquivos_saude (cadastro_id, nome_arquivo, tipo_arquivo, caminho_arquivo, descricao) VALUES (?, ?, ?, ?, ?)', 
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
    c = conn.cursor()
    
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
    c = conn.cursor()
    
    c.execute('SELECT nome_completo FROM cadastros WHERE id = ?', (cadastro_id,))
    cadastro = c.fetchone()
    
    c.execute('SELECT * FROM arquivos_saude WHERE cadastro_id = ? ORDER BY data_upload DESC', (cadastro_id,))
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
    c = conn.cursor()
    c.execute('SELECT nome_arquivo, caminho_arquivo FROM arquivos_saude WHERE id = ?', (arquivo_id,))
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
        c = conn.cursor()
        c.execute('INSERT INTO arquivos_saude (cadastro_id, nome_arquivo, tipo_arquivo, caminho_arquivo, descricao) VALUES (?, ?, ?, ?, ?)', 
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
    
    # Apenas admin pode acessar
    if session['usuario'] != 'admin':
        flash('Acesso negado. Apenas administradores podem gerenciar usuários.')
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT id, usuario FROM usuarios ORDER BY usuario')
    usuarios = c.fetchall()
    conn.close()
    
    return render_template('usuarios.html', usuarios=usuarios)

@app.route('/criar_usuario', methods=['GET', 'POST'])
def criar_usuario():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    # Apenas admin pode acessar
    if session['usuario'] != 'admin':
        flash('Acesso negado. Apenas administradores podem criar usuários.')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        novo_usuario = request.form['usuario']
        nova_senha = request.form['senha']
        
        if len(nova_senha) < 8:
            flash('Senha deve ter pelo menos 8 caracteres')
            return render_template('criar_usuario.html')
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # Verificar se usuário já existe
        c.execute('SELECT id FROM usuarios WHERE usuario = ?', (novo_usuario,))
        if c.fetchone():
            flash('Usuário já existe')
            conn.close()
            return render_template('criar_usuario.html')
        
        # Criar usuário
        senha_hash = generate_password_hash(nova_senha)
        c.execute('INSERT INTO usuarios (usuario, senha) VALUES (?, ?)', (novo_usuario, senha_hash))
        conn.commit()
        conn.close()
        
        flash('Usuário criado com sucesso')
        return redirect(url_for('usuarios'))
    
    return render_template('criar_usuario.html')

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
