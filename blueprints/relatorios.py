from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
from database import get_db_connection, listar_movimentacoes_caixa
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import csv
import io
import logging

logger = logging.getLogger(__name__)

relatorios_bp = Blueprint('relatorios', __name__)

@relatorios_bp.route('/relatorios')
def relatorios():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    return render_template('relatorios.html')

@relatorios_bp.route('/tipos_relatorios')
def tipos_relatorios():
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
        flash('Erro ao carregar relatório completo', 'error')
        return redirect(url_for('relatorios.relatorios'))

@relatorios_bp.route('/relatorio_caixa')
def relatorio_caixa():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    try:
        # Filtro por tipo (entrada/saida)
        tipo = request.args.get('tipo')
        
        # Obter todas as movimentações
        movimentacoes = listar_movimentacoes_caixa(limit=1000, tipo=tipo if tipo else None)
        
        # Calcular totais
        total_entradas = sum(mov['valor'] for mov in movimentacoes if mov['tipo'] == 'entrada')
        total_saidas = sum(mov['valor'] for mov in movimentacoes if mov['tipo'] == 'saida')
        saldo_total = total_entradas - total_saidas
        
        return render_template('relatorio_caixa.html',
                             movimentacoes=movimentacoes,
                             total_entradas=total_entradas,
                             total_saidas=total_saidas,
                             saldo_total=saldo_total,
                             tipo_filtro=tipo)
    
    except Exception as e:
        logger.error(f"Erro ao gerar relatório de caixa: {e}")
        flash('Erro ao gerar relatório', 'error')
        return redirect(url_for('caixa.caixa'))

@relatorios_bp.route('/exportar/<tipo>')
def exportar(tipo):
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    formato = request.args.get('formato', 'csv')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Definir query baseada no tipo
        if tipo == 'completo':
            query = 'SELECT * FROM cadastros ORDER BY nome_completo'
            filename = 'relatorio_completo'
        elif tipo == 'caixa':
            filtro_tipo = request.args.get('filtro_tipo')
            query = '''SELECT mc.id, mc.tipo, mc.valor, mc.descricao, 
                       mc.nome_pessoa, mc.numero_recibo, mc.observacoes, mc.data_movimentacao, 
                       mc.usuario, c.nome_completo as titular_cadastro
                       FROM movimentacoes_caixa mc
                       LEFT JOIN cadastros c ON mc.cadastro_id = c.id'''
            
            if filtro_tipo in ['entrada', 'saida']:
                query += f" WHERE mc.tipo = '{filtro_tipo}'"
                filename = f'relatorio_caixa_{filtro_tipo}'
            else:
                filename = 'relatorio_caixa'
                
            query += ' ORDER BY mc.data_movimentacao DESC'
        
        cursor.execute(query)
        dados = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if formato == 'csv':
            return exportar_csv(dados, tipo, filename)
        elif formato == 'pdf':
            return exportar_pdf(dados, tipo, filename)
            
    except Exception as e:
        logger.error(f"Erro ao exportar {tipo}: {e}")
        flash('Erro ao exportar dados', 'error')
        return redirect(url_for('relatorios.relatorios'))

def exportar_csv(dados, tipo, filename):
    """Exporta dados para CSV"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    if tipo == 'completo':
        # Cabeçalho para cadastros
        writer.writerow(['ID', 'Nome', 'CPF', 'Telefone', 'Bairro', 'Renda Familiar'])
        for row in dados:
            writer.writerow([row[0], row[1], row[2], row[4], row[6], row[13]])
    elif tipo == 'caixa':
        # Cabeçalho para caixa
        writer.writerow(['ID', 'Tipo', 'Valor', 'Descrição', 'Titular Cadastro', 'Nome Pessoa', 
                       'Número Recibo', 'Observações', 'Data', 'Usuário'])
        for row in dados:
            writer.writerow(row)
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        as_attachment=True,
        download_name=f'{filename}.csv',
        mimetype='text/csv'
    )

def exportar_pdf(dados, tipo, filename):
    """Exporta dados para PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []
    
    # Título
    if tipo == 'completo':
        title = Paragraph("AMEG - Relatório Completo de Cadastros", styles['Title'])
    elif tipo == 'caixa':
        filtro_tipo = request.args.get('filtro_tipo')
        if filtro_tipo == 'entrada':
            title = Paragraph("AMEG - Relatório de Entradas do Caixa", styles['Title'])
        elif filtro_tipo == 'saida':
            title = Paragraph("AMEG - Relatório de Saídas do Caixa", styles['Title'])
        else:
            title = Paragraph("AMEG - Relatório de Movimentações do Caixa", styles['Title'])
    
    elements.append(title)
    elements.append(Spacer(1, 20))
    
    # Criar tabela com dados
    if tipo == 'completo':
        table_data = [['Nome', 'CPF', 'Telefone', 'Bairro']]
        for row in dados:
            table_data.append([row[1], row[2], row[4], row[6]])
    elif tipo == 'caixa':
        table_data = [['Tipo', 'Valor', 'Descrição', 'Data']]
        for row in dados:
            table_data.append([
                row[1].title(),
                f"R$ {row[2]:.2f}",
                row[3][:50] + '...' if len(row[3]) > 50 else row[3],
                row[7].strftime('%d/%m/%Y')
            ])
    
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
    
    return send_file(buffer, as_attachment=True, download_name=f'{filename}.pdf', mimetype='application/pdf')
