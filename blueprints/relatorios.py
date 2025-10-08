from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
from database import get_db_connection, listar_movimentacoes_caixa
import psycopg2.extras
import csv
import io
import logging
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from docx import Document
from docx.shared import Inches

logger = logging.getLogger(__name__)

relatorios_bp = Blueprint('relatorios', __name__)

@relatorios_bp.route('/relatorios')
def relatorios():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    return render_template('tipos_relatorios.html')

@relatorios_bp.route('/relatorio_completo')
def relatorio_completo():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    # Paginação
    page = int(request.args.get('page', 1))
    per_page = 50
    offset = (page - 1) * per_page
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Contar total de registros
        cursor.execute('SELECT COUNT(*) FROM cadastros')
        total_records = cursor.fetchone()[0]
        total_pages = (total_records + per_page - 1) // per_page
        
        # Buscar cadastros paginados
        cursor.execute('SELECT * FROM cadastros ORDER BY nome_completo LIMIT %s OFFSET %s', 
                        (per_page, offset))
        cadastros = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('relatorio_completo.html', 
                             cadastros=cadastros,
                             page=page,
                             total_pages=total_pages,
                             total_records=total_records)
        
    except Exception as e:
        logger.error(f"Erro em relatorio_completo: {e}")
        flash('Erro ao carregar relatório completo.')
        return redirect(url_for('relatorios.relatorios'))

@relatorios_bp.route('/relatorio_simplificado')
def relatorio_simplificado():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = 'SELECT nome_completo, telefone, bairro, renda_familiar FROM cadastros ORDER BY nome_completo'
        cursor.execute(query)
        cadastros = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('relatorio_simplificado.html', cadastros=cadastros)
        
    except Exception as e:
        logger.error(f"Erro em relatorio_simplificado: {e}")
        flash('Erro ao carregar relatório simplificado.')
        return redirect(url_for('relatorios.relatorios'))

@relatorios_bp.route('/relatorio_estatistico')
def relatorio_estatistico():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Estatísticas gerais
        cursor.execute('SELECT COUNT(*) FROM cadastros')
        total = cursor.fetchone()[0]
        
        # Por bairro
        cursor.execute('SELECT bairro, COUNT(*) FROM cadastros GROUP BY bairro ORDER BY COUNT(*) DESC')
        por_bairro = cursor.fetchall()
        
        # Por gênero
        cursor.execute('SELECT genero, COUNT(*) FROM cadastros GROUP BY genero')
        por_genero = cursor.fetchall()
        
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
        
        cursor.close()
        conn.close()
        
        stats = {
            'total': total,
            'por_bairro': por_bairro,
            'por_genero': por_genero,
            'por_idade': por_idade
        }
        
        return render_template('relatorio_estatistico.html', stats=stats)
        
    except Exception as e:
        logger.error(f"Erro em relatorio_estatistico: {e}")
        flash('Erro ao carregar relatório estatístico.')
        return redirect(url_for('relatorios.relatorios'))

@relatorios_bp.route('/relatorio_por_bairro')
def relatorio_por_bairro():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Query simplificada
        query = '''SELECT bairro, COUNT(*) as total, 
                   AVG(renda_familiar) as renda_media
                   FROM cadastros 
                   WHERE bairro IS NOT NULL AND bairro != ''
                   GROUP BY bairro 
                   ORDER BY total DESC'''
        cursor.execute(query)
        bairros = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('relatorio_por_bairro.html', bairros=bairros)
        
    except Exception as e:
        logger.error(f"Erro em relatorio_por_bairro: {e}")
        return render_template('relatorio_por_bairro.html', bairros=[], erro=f"Erro: {str(e)}")

@relatorios_bp.route('/relatorio_renda')
def relatorio_renda():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Faixas de renda
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
        cursor.execute(query1)
        faixas_renda = cursor.fetchall()
        
        # Renda por bairro
        query2 = '''SELECT bairro, 
                     AVG(renda_familiar) as renda_media, 
                     COUNT(*) as total
                     FROM cadastros 
                     WHERE bairro IS NOT NULL AND bairro != ''
                     GROUP BY bairro 
                     ORDER BY renda_media DESC NULLS LAST'''
        cursor.execute(query2)
        renda_bairro = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('relatorio_renda.html', faixas_renda=faixas_renda, renda_bairro=renda_bairro)
        
    except Exception as e:
        logger.error(f"Erro em relatorio_renda: {e}")
        flash('Erro ao carregar relatório de renda.')
        return redirect(url_for('relatorios.relatorios'))

@relatorios_bp.route('/relatorio_saude')
def relatorio_saude():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    # Parâmetros de filtro
    busca_nome = request.args.get('busca_nome', '').strip()
    ordem = request.args.get('ordem', 'asc')
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
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

@relatorios_bp.route('/exportar')
def exportar():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    tipo = request.args.get('tipo', 'completo')
    formato = request.args.get('formato', 'csv')
    cadastro_id = request.args.get('cadastro_id')
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
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
    elif tipo == 'caixa':
        filtro_tipo = request.args.get('filtro_tipo')
        
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
                if tipo != 'caixa':
                    row_data = [
                        row[1] if hasattr(row, '__getitem__') else getattr(row, 'nome_completo', ''),
                        row[6] if hasattr(row, '__getitem__') else getattr(row, 'telefone', ''),
                        row[2] if hasattr(row, '__getitem__') else getattr(row, 'endereco', ''),
                        row[3] if hasattr(row, '__getitem__') else getattr(row, 'numero', ''),
                        row[4] if hasattr(row, '__getitem__') else getattr(row, 'bairro', ''),
                        row[5] if hasattr(row, '__getitem__') else getattr(row, 'cep', ''),
                        row[8] if hasattr(row, '__getitem__') else getattr(row, 'genero', ''),
                        row[9] if hasattr(row, '__getitem__') else getattr(row, 'idade', ''),
                        row[13] if hasattr(row, '__getitem__') else getattr(row, 'cpf', ''),
                        row[14] if hasattr(row, '__getitem__') else getattr(row, 'rg', ''),
                        row[16] if hasattr(row, '__getitem__') else getattr(row, 'estado_civil', ''),
                        row[17] if hasattr(row, '__getitem__') else getattr(row, 'escolaridade', ''),
                        row[40] if hasattr(row, '__getitem__') else getattr(row, 'renda_familiar', '')
                    ]
                    writer.writerow(row_data)
        
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'{filename}.csv'
        )
    
    elif formato == 'pdf':
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Center
        )
        
        if tipo == 'completo':
            if cadastro_id:
                elements.append(Paragraph(f"Ficha Individual - Cadastro {cadastro_id}", title_style))
            else:
                elements.append(Paragraph("Relatório Completo de Cadastros", title_style))
        elif tipo == 'simplificado':
            elements.append(Paragraph("Relatório Simplificado", title_style))
        elif tipo == 'caixa':
            elements.append(Paragraph("Relatório de Movimentações do Caixa", title_style))
        
        elements.append(Spacer(1, 12))
        
        # Preparar dados para tabela
        if tipo == 'simplificado':
            table_data = [['Nome', 'Telefone', 'Bairro', 'Renda Familiar']]
            for row in dados:
                table_data.append([
                    str(row['nome_completo'] or ''),
                    str(row['telefone'] or ''),
                    str(row['bairro'] or ''),
                    f"R$ {row['renda_familiar']:.2f}" if row['renda_familiar'] else ''
                ])
        elif tipo == 'caixa':
            table_data = [['Tipo', 'Valor', 'Descrição', 'Data']]
            for row in dados:
                table_data.append([
                    str(row['tipo'].title() if row['tipo'] else ''),
                    f"R$ {row['valor']:.2f}" if row['valor'] else '',
                    str(row['descricao'] or ''),
                    row['data_movimentacao'].strftime('%d/%m/%Y') if row['data_movimentacao'] else ''
                ])
        else:
            # Relatório completo
            table_data = [['Nome', 'Telefone', 'Bairro', 'CPF', 'Renda']]
            for row in dados:
                table_data.append([
                    str(row['nome_completo'] or ''),
                    str(row['telefone'] or ''),
                    str(row['bairro'] or ''),
                    str(row['cpf'] or ''),
                    f"R$ {row['renda_familiar']:.2f}" if row['renda_familiar'] else ''
                ])
        
        # Criar tabela
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
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
    return redirect(url_for('relatorios.relatorios'))
