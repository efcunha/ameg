from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
from database import get_db_connection, registrar_auditoria
from werkzeug.utils import secure_filename
import psycopg2.extras
import io
import logging
import traceback

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
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
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
        cursor.execute(query_cadastros)
        cadastros_data = cursor.fetchall()
        
        cadastros = []
        for cadastro_data in cadastros_data:
            # Buscar arquivos de saúde para cada cadastro
            query_arquivos = '''
                SELECT id, tipo_arquivo, nome_arquivo, descricao, data_upload
                FROM arquivos_saude 
                WHERE cadastro_id = %s
                ORDER BY data_upload DESC
            '''
            cursor.execute(query_arquivos, (cadastro_data['id'],))
            arquivos = cursor.fetchall()
            
            cadastro_obj = {
                'id': cadastro_data['id'],
                'nome_completo': cadastro_data['nome_completo'],
                'cpf': cadastro_data['cpf'],
                'arquivos_count': cadastro_data['arquivos_count'],
                'arquivos_saude': arquivos
            }
            cadastros.append(cadastro_obj)
        
        cursor.close()
        conn.close()
        
        # Verificar permissão do caixa
        return render_template('arquivos_cadastros.html', cadastros=cadastros)
        
    except Exception as e:
        logger.error(f"Erro em arquivos_cadastros: {e}")
        flash(f'Erro ao carregar arquivos: {str(e)}', 'error')
        return redirect(url_for('dashboard.dashboard'))

@arquivos_bp.route('/exportar_arquivos_pdf/<int:cadastro_id>')
def exportar_arquivos_pdf(cadastro_id,):
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Buscar dados do cadastro
        query_cadastro = 'SELECT * FROM cadastros WHERE id = %s'
        cursor.execute(query_cadastro, (cadastro_id,))
        cadastro = cursor.fetchone()
        
        if not cadastro:
            cursor.close()
            conn.close()
            return "Cadastro não encontrado", 404
        
        # Buscar arquivos de saúde
        query_arquivos = '''
            SELECT tipo_arquivo, nome_arquivo, descricao, data_upload, caminho_arquivo
            FROM arquivos_saude 
            WHERE cadastro_id = %s
            ORDER BY tipo_arquivo, data_upload
        '''
        cursor.execute(query_arquivos, (cadastro_id,))
        arquivos = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Gerar PDF
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from io import BytesIO
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch)
        styles = getSampleStyleSheet()
        story = []
        
        # Título
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, spaceAfter=20)
        story.append(Paragraph(f"Relatório de Arquivos de Saúde", title_style))
        
        # Dados do cadastro
        nome = cadastro[1] or 'N/A'
        cpf = cadastro[13] or 'N/A'
        telefone = cadastro[6] or 'N/A'
        
        story.append(Paragraph(f"<b>Nome:</b> {nome}", styles['Normal']))
        story.append(Paragraph(f"<b>CPF:</b> {cpf}", styles['Normal']))
        story.append(Paragraph(f"<b>Telefone:</b> {telefone}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Lista de arquivos
        if arquivos:
            story.append(Paragraph("<b>Arquivos de Saúde Anexados:</b>", styles['Heading2']))
            story.append(Spacer(1, 10))
            
            # Agrupar por tipo
            tipos = {}
            for arquivo in arquivos:
                tipo = arquivo[0]
                if tipo not in tipos:
                    tipos[tipo] = []
                tipos[tipo].append(arquivo)
            
            for tipo, lista_arquivos in tipos.items():
                story.append(Paragraph(f"<b>{tipo.title()}:</b>", styles['Heading3']))
                
                for arquivo in lista_arquivos:
                    story.append(Paragraph(f"• {arquivo[1]}", styles['Normal']))
                    if arquivo[2]:  # descrição
                        story.append(Paragraph(f"  <i>{arquivo[2]}</i>", styles['Normal']))
                    story.append(Paragraph(f"  Data: {arquivo[3].strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
                    story.append(Spacer(1, 5))
                
                story.append(Spacer(1, 10))
        else:
            story.append(Paragraph("Nenhum arquivo de saúde anexado.", styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        
        filename = f'arquivos_saude_{nome.replace(" ", "_")}.pdf'
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"Erro em exportar_arquivos_pdf: {e}")
        flash(f'Erro ao gerar PDF: {str(e)}', 'error')
        return redirect(url_for('arquivos.arquivos_cadastros'))

@arquivos_bp.route('/arquivos_saude/<int:cadastro_id>')
def arquivos_saude(cadastro_id,):
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT nome_completo FROM cadastros WHERE id = %s', (cadastro_id,))
    cadastro = cursor.fetchone()
    
    cursor.execute('SELECT * FROM arquivos_saude WHERE cadastro_id = %s ORDER BY data_upload DESC', (cadastro_id,))
    arquivos = cursor.fetchall()
    
    conn.close()
    
    if not cadastro:
        flash('Cadastro não encontrado!')
        return redirect(url_for('relatorios.relatorio_saude'))
    
    return render_template('arquivos_saude.html', cadastro=cadastro, arquivos=arquivos, cadastro_id=cadastro_id)

@arquivos_bp.route('/download_arquivo/<int:arquivo_id>')
def download_arquivo(arquivo_id,):
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('SELECT nome_arquivo, arquivo_dados, tipo_arquivo FROM arquivos_saude WHERE id = %s', (arquivo_id,))
        arquivo = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not arquivo or not arquivo['arquivo_dados']:
            flash('Arquivo não encontrado!')
            return redirect(url_for('arquivos.arquivos_cadastros'))
        
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
        return redirect(url_for('arquivos.arquivos_cadastros'))

@arquivos_bp.route('/upload_arquivo/<int:cadastro_id>', methods=['POST'])
def upload_arquivo(cadastro_id,):
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    if 'arquivo' not in request.files:
        flash('Nenhum arquivo selecionado!')
        return redirect(url_for('arquivos.arquivos_saude', cadastro_id=cadastro_id))
    
    file = request.files['arquivo']
    if file.filename == '':
        flash('Nenhum arquivo selecionado!')
        return redirect(url_for('arquivos.arquivos_saude', cadastro_id=cadastro_id))
    
    if file and allowed_file(file.filename):
        file_data = file.read()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO arquivos_saude (cadastro_id, nome_arquivo, tipo_arquivo, arquivo_dados, descricao) VALUES (%s, %s, %s, %s, %s)', 
                (cadastro_id, file.filename, request.form.get('tipo_arquivo'), file_data, request.form.get('descricao')))
        conn.commit()
        conn.close()
        
        flash('Arquivo enviado com sucesso!')
    else:
        flash('Tipo de arquivo não permitido! Use: PDF, PNG, JPG, DOC, DOCX')
    
    return redirect(url_for('arquivos.arquivos_saude', cadastro_id=cadastro_id))

@arquivos_bp.route('/excluir_arquivo/<int:arquivo_id>')
def excluir_arquivo(arquivo_id,):
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Buscar o cadastro_id antes de excluir
        cursor.execute('SELECT cadastro_id FROM arquivos_saude WHERE id = %s', (arquivo_id,))
        
        result = cursor.fetchone()
        if not result:
            flash('Arquivo não encontrado!')
            return redirect(url_for('dashboard.dashboard'))
        
        cadastro_id = result[0] if isinstance(result, tuple) else result['cadastro_id']
        
        # Excluir o arquivo
        cursor.execute('DELETE FROM arquivos_saude WHERE id = %s', (arquivo_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Arquivo excluído com sucesso!')
        return redirect(url_for('cadastros.editar_cadastro', cadastro_id=cadastro_id))
        
    except Exception as e:
        logger.error(f"Erro ao excluir arquivo: {e}")
        flash('Erro ao excluir arquivo.')
        return redirect(url_for('dashboard.dashboard'))
