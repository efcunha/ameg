from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
from database import (get_db_connection, inserir_movimentacao_caixa, inserir_comprovante_caixa, 
                     listar_movimentacoes_caixa, obter_saldo_caixa, listar_cadastros_simples, 
                     usuario_tem_permissao, registrar_auditoria, obter_comprovantes_movimentacao)
import psycopg2.extras
import logging
import io

logger = logging.getLogger(__name__)

# Criar blueprint
caixa_bp = Blueprint('caixa', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@caixa_bp.route('/caixa')
def caixa():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    # Verificar permissão de caixa
    if not usuario_tem_permissao(session['usuario'], 'caixa'):
        flash('Você não tem permissão para acessar o sistema de caixa', 'error')
        return redirect(url_for('dashboard.dashboard'))
    
    try:
        logger.info("=== INICIANDO CAIXA ===")
        logger.info(f"Usuário autenticado: {session['usuario']}")
        
        # Obter saldo atual
        logger.info("Tentando obter saldo do caixa...")
        saldo = obter_saldo_caixa()
        logger.info(f"Saldo obtido com sucesso: {saldo}")
        
        # Obter lista de pessoas cadastradas
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
        return redirect(url_for('dashboard.dashboard'))

@caixa_bp.route('/caixa', methods=['POST'])
def processar_movimentacao_caixa():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    if not usuario_tem_permissao(session['usuario'], 'caixa'):
        flash('Você não tem permissão para usar o sistema de caixa', 'error')
        return redirect(url_for('dashboard.dashboard'))
    
    try:
        # Obter dados do formulário
        tipo = request.form.get('tipo')
        valor = float(request.form.get('valor', 0))
        descricao = request.form.get('descricao', '').strip()
        cadastro_id = request.form.get('cadastro_id') or None
        nome_pessoa = request.form.get('nome_pessoa', '').strip()
        numero_recibo = request.form.get('numero_recibo', '').strip()
        observacoes = request.form.get('observacoes', '').strip()
        
        # Validações
        if not descricao:
            flash('Descrição é obrigatória', 'error')
            return redirect(url_for('caixa.caixa'))
        
        if valor <= 0:
            flash('Valor deve ser maior que zero', 'error')
            return redirect(url_for('caixa.caixa'))
        
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
        return redirect(url_for('caixa.caixa'))
    
    except Exception as e:
        logger.error(f"Erro ao processar movimentação: {e}")
        flash('Erro ao registrar movimentação', 'error')
        return redirect(url_for('caixa.caixa'))

# Adicionar outras rotas do caixa aqui...

@caixa_bp.route('/visualizar_comprovantes/<int:movimentacao_id>')
def visualizar_comprovantes(movimentacao_id):
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    if not usuario_tem_permissao(session['usuario'], 'caixa'):
        flash('Você não tem permissão para visualizar comprovantes', 'error')
        return redirect(url_for('dashboard.dashboard'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Buscar dados da movimentação
        cursor.execute('SELECT * FROM movimentacoes_caixa WHERE id = %s', (movimentacao_id,))
        movimentacao = cursor.fetchone()
        
        if not movimentacao:
            flash('Movimentação não encontrada', 'error')
            return redirect(url_for('caixa.caixa'))
        
        # Buscar comprovantes
        comprovantes = obter_comprovantes_movimentacao(movimentacao_id)
        
        cursor.close()
        conn.close()
        
        return render_template('visualizar_comprovantes.html', 
                             movimentacao=movimentacao, 
                             comprovantes=comprovantes)
    
    except Exception as e:
        logger.error(f"Erro ao visualizar comprovantes: {e}")
        flash('Erro ao carregar comprovantes', 'error')
        return redirect(url_for('caixa.caixa'))

@caixa_bp.route('/download_comprovante/<int:comprovante_id>')
def download_comprovante(comprovante_id):
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    if not usuario_tem_permissao(session['usuario'], 'caixa'):
        flash('Você não tem permissão para baixar comprovantes', 'error')
        return redirect(url_for('dashboard.dashboard'))
    
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
            return redirect(url_for('caixa.caixa'))
        
        return send_file(
            io.BytesIO(comprovante[2]),
            as_attachment=True,
            download_name=comprovante[0],
            mimetype=comprovante[1]
        )
    
    except Exception as e:
        logger.error(f"Erro ao baixar comprovante: {e}")
        flash('Erro ao baixar comprovante', 'error')
        return redirect(url_for('caixa.caixa'))

@caixa_bp.route('/exportar_comprovantes_pdf/<int:movimentacao_id>')
def exportar_comprovantes_pdf(movimentacao_id):
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    if not usuario_tem_permissao(session['usuario'], 'caixa'):
        flash('Você não tem permissão para exportar comprovantes', 'error')
        return redirect(url_for('dashboard.dashboard'))
    
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        import io
        from PIL import Image as PILImage
        import PyPDF2
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Buscar dados da movimentação
        cursor.execute('SELECT * FROM movimentacoes_caixa WHERE id = %s', (movimentacao_id,))
        movimentacao = cursor.fetchone()
        
        if not movimentacao:
            flash('Movimentação não encontrada', 'error')
            return redirect(url_for('caixa.caixa'))
        
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
                        # Para PDFs, extrair e incorporar conteúdo
                        try:
                            pdf_buffer = io.BytesIO(arquivo_dados)
                            pdf_reader = PyPDF2.PdfReader(pdf_buffer)
                            
                            elements.append(Paragraph(f"📄 Arquivo PDF: {comp['nome_arquivo']}", styles['Heading4']))
                            elements.append(Spacer(1, 10))
                            
                            # Extrair texto de cada página
                            total_pages = len(pdf_reader.pages)
                            logger.info(f"🔍 PDF {comp['nome_arquivo']} tem {total_pages} páginas")
                            
                            for page_num, page in enumerate(pdf_reader.pages, 1):
                                try:
                                    text = page.extract_text()
                                    logger.info(f"📄 Página {page_num}: {len(text)} caracteres extraídos")
                                    
                                    if text.strip():
                                        elements.append(Paragraph(f"Página {page_num}:", styles['Normal']))
                                        # Limitar texto para evitar PDFs muito grandes
                                        text_preview = text[:1500] + "..." if len(text) > 1500 else text
                                        elements.append(Paragraph(text_preview, styles['Normal']))
                                        elements.append(Spacer(1, 10))
                                    else:
                                        elements.append(Paragraph(f"Página {page_num}: (sem texto extraível)", styles['Italic']))
                                        
                                except Exception as page_error:
                                    logger.error(f"❌ Erro na página {page_num}: {page_error}")
                                    elements.append(Paragraph(f"Página {page_num}: (erro ao extrair texto)", styles['Italic']))
                            
                        except Exception as pdf_error:
                            logger.error(f"❌ Erro ao processar PDF {comp['nome_arquivo']}: {pdf_error}")
                            elements.append(Paragraph(f"📄 Arquivo PDF: {comp['nome_arquivo']}", styles['Normal']))
                            elements.append(Paragraph("(Erro ao extrair conteúdo do PDF)", styles['Italic']))
                        
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
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"Erro ao exportar comprovantes PDF: {e}")
        flash('Erro ao exportar comprovantes em PDF', 'error')
        return redirect(url_for('caixa.caixa'))
