from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
from database import get_db_connection, registrar_auditoria
import io
import logging

logger = logging.getLogger(__name__)

arquivos_bp = Blueprint('arquivos', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@arquivos_bp.route('/arquivos_cadastros')
def arquivos_cadastros():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Buscar cadastros com arquivos
        cursor.execute('''
            SELECT c.id, c.nome_completo, COUNT(a.id) as total_arquivos
            FROM cadastros c
            LEFT JOIN arquivos_saude a ON c.id = a.cadastro_id
            GROUP BY c.id, c.nome_completo
            HAVING COUNT(a.id) > 0
            ORDER BY c.nome_completo
        ''')
        cadastros_com_arquivos = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('arquivos_cadastros.html', cadastros=cadastros_com_arquivos)
    
    except Exception as e:
        logger.error(f"Erro ao listar arquivos: {e}")
        flash('Erro ao carregar arquivos', 'error')
        return redirect(url_for('dashboard.dashboard'))

@arquivos_bp.route('/arquivos_saude/<int:cadastro_id>')
def arquivos_saude(cadastro_id):
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Buscar dados do cadastro
        cursor.execute('SELECT nome_completo FROM cadastros WHERE id = %s', (cadastro_id,))
        cadastro = cursor.fetchone()
        
        if not cadastro:
            flash('Cadastro não encontrado', 'error')
            return redirect(url_for('arquivos.arquivos_cadastros'))
        
        # Buscar arquivos de saúde
        cursor.execute('''
            SELECT id, nome_arquivo, tipo_arquivo, data_upload, tamanho_arquivo
            FROM arquivos_saude 
            WHERE cadastro_id = %s 
            ORDER BY data_upload DESC
        ''', (cadastro_id,))
        arquivos = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('arquivos_saude.html', 
                             cadastro=cadastro, 
                             arquivos=arquivos, 
                             cadastro_id=cadastro_id)
    
    except Exception as e:
        logger.error(f"Erro ao listar arquivos de saúde: {e}")
        flash('Erro ao carregar arquivos de saúde', 'error')
        return redirect(url_for('arquivos.arquivos_cadastros'))

@arquivos_bp.route('/upload_arquivo_saude/<int:cadastro_id>', methods=['POST'])
def upload_arquivo_saude(cadastro_id):
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    try:
        if 'arquivo' not in request.files:
            flash('Nenhum arquivo selecionado', 'error')
            return redirect(url_for('arquivos.arquivos_saude', cadastro_id=cadastro_id))
        
        arquivo = request.files['arquivo']
        
        if arquivo.filename == '':
            flash('Nenhum arquivo selecionado', 'error')
            return redirect(url_for('arquivos.arquivos_saude', cadastro_id=cadastro_id))
        
        if not allowed_file(arquivo.filename):
            flash('Tipo de arquivo não permitido', 'error')
            return redirect(url_for('arquivos.arquivos_saude', cadastro_id=cadastro_id))
        
        # Verificar tamanho (16MB máximo)
        arquivo.seek(0, 2)
        size = arquivo.tell()
        arquivo.seek(0)
        
        if size > 16 * 1024 * 1024:
            flash('Arquivo muito grande (máximo 16MB)', 'error')
            return redirect(url_for('arquivos.arquivos_saude', cadastro_id=cadastro_id))
        
        # Salvar arquivo
        arquivo_dados = arquivo.read()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO arquivos_saude (cadastro_id, nome_arquivo, tipo_arquivo, arquivo_dados, tamanho_arquivo)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        ''', (cadastro_id, arquivo.filename, arquivo.content_type, arquivo_dados, size))
        
        arquivo_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        # Registrar auditoria
        registrar_auditoria(
            session['usuario'], 'INSERT', 'arquivos_saude', arquivo_id,
            None, f"Arquivo de saúde enviado: {arquivo.filename} (Cadastro ID: {cadastro_id})"
        )
        
        flash('Arquivo enviado com sucesso!', 'success')
        
    except Exception as e:
        logger.error(f"Erro ao fazer upload: {e}")
        flash('Erro ao enviar arquivo', 'error')
    
    return redirect(url_for('arquivos.arquivos_saude', cadastro_id=cadastro_id))

@arquivos_bp.route('/download_arquivo/<int:arquivo_id>')
def download_arquivo(arquivo_id):
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT nome_arquivo, tipo_arquivo, arquivo_dados
            FROM arquivos_saude
            WHERE id = %s
        ''', (arquivo_id,))
        
        arquivo = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not arquivo:
            flash('Arquivo não encontrado', 'error')
            return redirect(url_for('arquivos.arquivos_cadastros'))
        
        return send_file(
            io.BytesIO(arquivo[2]),
            as_attachment=True,
            download_name=arquivo[0],
            mimetype=arquivo[1]
        )
    
    except Exception as e:
        logger.error(f"Erro ao baixar arquivo: {e}")
        flash('Erro ao baixar arquivo', 'error')
        return redirect(url_for('arquivos.arquivos_cadastros'))

@arquivos_bp.route('/excluir_arquivo/<int:arquivo_id>')
def excluir_arquivo(arquivo_id):
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Buscar dados do arquivo para auditoria
        cursor.execute('''
            SELECT cadastro_id, nome_arquivo 
            FROM arquivos_saude 
            WHERE id = %s
        ''', (arquivo_id,))
        arquivo_data = cursor.fetchone()
        
        if not arquivo_data:
            flash('Arquivo não encontrado', 'error')
            return redirect(url_for('arquivos.arquivos_cadastros'))
        
        # Excluir arquivo
        cursor.execute('DELETE FROM arquivos_saude WHERE id = %s', (arquivo_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        # Registrar auditoria
        registrar_auditoria(
            session['usuario'], 'DELETE', 'arquivos_saude', arquivo_id,
            str(arquivo_data), f"Arquivo excluído: {arquivo_data[1]}"
        )
        
        flash('Arquivo excluído com sucesso!', 'success')
        return redirect(url_for('arquivos.arquivos_saude', cadastro_id=arquivo_data[0]))
        
    except Exception as e:
        logger.error(f"Erro ao excluir arquivo: {e}")
        flash('Erro ao excluir arquivo', 'error')
        return redirect(url_for('arquivos.arquivos_cadastros'))
