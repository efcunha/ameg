from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
from database import get_db_connection, registrar_auditoria, usuario_tem_permissao, inserir_movimentacao_caixa, inserir_comprovante_caixa, listar_movimentacoes_caixa, obter_saldo_caixa, listar_cadastros_simples, obter_comprovantes_movimentacao
import psycopg2.extras
import io
import logging

logger = logging.getLogger(__name__)

caixa_bp = Blueprint('caixa', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@caixa_bp.route('/caixa', methods=['GET', 'POST'])
def caixa():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    # Verificar permissão de caixa
    if not usuario_tem_permissao(session['usuario'], 'caixa'):
        flash('Você não tem permissão para acessar o sistema de caixa', 'error')
        return redirect(url_for('dashboard.dashboard'))
    
    if request.method == 'POST':
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
            
            for comprovante in comprovantes:
                if comprovante and comprovante.filename:
                    # Validar tipo de arquivo
                    if not allowed_file(comprovante.filename):
                        flash(f'Tipo de arquivo não permitido: {comprovante.filename}', 'error')
                        continue
                    
                    # Validar tamanho (16MB máximo)
                    comprovante.seek(0, 2)  # Ir para o final
                    size = comprovante.tell()
                    comprovante.seek(0)  # Voltar ao início
                    
                    if size > 16 * 1024 * 1024:  # 16MB
                        flash(f'Arquivo muito grande: {comprovante.filename}', 'error')
                        continue
                    
                    # Salvar comprovante
                    arquivo_dados = comprovante.read()
                    inserir_comprovante_caixa(
                        movimentacao_id, 
                        comprovante.filename,
                        comprovante.content_type,
                        arquivo_dados
                    )
            
            flash(f'Movimentação de {tipo} registrada com sucesso!', 'success')
            return redirect(url_for('caixa.caixa'))
        
        except Exception as e:
            logger.error(f"Erro ao processar movimentação: {e}")
            flash('Erro ao registrar movimentação', 'error')
            return redirect(url_for('caixa.caixa'))
    
    try:
        # Obter saldo atual
        saldo = obter_saldo_caixa()
        
        # Obter pessoas cadastradas para o select
        pessoas = listar_cadastros_simples()
        
        # Obter últimas movimentações
        movimentacoes = listar_movimentacoes_caixa(limit=20)
        
        return render_template('caixa.html', 
                             saldo=saldo, 
                             pessoas=pessoas, 
                             movimentacoes=movimentacoes)
    
    except Exception as e:
        logger.error(f"Erro ao carregar caixa: {e}")
        flash('Erro ao carregar sistema de caixa', 'error')
        return redirect(url_for('dashboard.dashboard'))

@caixa_bp.route('/relatorio_caixa')
def relatorio_caixa():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
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
        return redirect(url_for('caixa.caixa'))

@caixa_bp.route('/excluir_movimentacao/<int:movimentacao_id>')
def excluir_movimentacao(movimentacao_id):
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    if not usuario_tem_permissao(session['usuario'], 'caixa'):
        flash('Você não tem permissão para excluir movimentações', 'error')
        return redirect(url_for('dashboard.dashboard'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Buscar dados da movimentação para auditoria
        cursor.execute('SELECT * FROM movimentacoes_caixa WHERE id = %s', (movimentacao_id,))
        movimentacao = cursor.fetchone()
        
        if not movimentacao:
            flash('Movimentação não encontrada', 'error')
            return redirect(url_for('caixa.caixa'))
        
        # Excluir movimentação (comprovantes são excluídos automaticamente por CASCADE)
        cursor.execute('DELETE FROM movimentacoes_caixa WHERE id = %s', (movimentacao_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Registrar auditoria
        registrar_auditoria(
            session['usuario'], 'DELETE', 'movimentacoes_caixa', 
            movimentacao_id, str(movimentacao), None
        )
        
        flash('Movimentação excluída com sucesso!', 'success')
        return redirect(url_for('caixa.caixa'))
    
    except Exception as e:
        logger.error(f"Erro ao excluir movimentação: {e}")
        flash('Erro ao excluir movimentação', 'error')
        return redirect(url_for('caixa.caixa'))

@caixa_bp.route('/editar_movimentacao/<int:movimentacao_id>', methods=['GET', 'POST'])
def editar_movimentacao(movimentacao_id):
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    if not usuario_tem_permissao(session['usuario'], 'caixa'):
        flash('Você não tem permissão para editar movimentações', 'error')
        return redirect(url_for('dashboard.dashboard'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        if request.method == 'GET':
            # Buscar dados da movimentação
            cursor.execute('SELECT * FROM movimentacoes_caixa WHERE id = %s', (movimentacao_id,))
            movimentacao = cursor.fetchone()
            
            if not movimentacao:
                flash('Movimentação não encontrada', 'error')
                return redirect(url_for('caixa.caixa'))
            
            # Buscar pessoas cadastradas
            pessoas = listar_cadastros_simples()
            
            cursor.close()
            conn.close()
            
            return render_template('editar_movimentacao.html', 
                                 movimentacao=movimentacao, 
                                 pessoas=pessoas)
        
        elif request.method == 'POST':
            # Buscar dados atuais para auditoria
            cursor.execute('SELECT * FROM movimentacoes_caixa WHERE id = %s', (movimentacao_id,))
            dados_anteriores = cursor.fetchone()
            
            if not dados_anteriores:
                flash('Movimentação não encontrada', 'error')
                return redirect(url_for('caixa.caixa'))
            
            # Processar dados do formulário
            tipo = request.form.get('tipo')
            valor_str = request.form.get('valor', '0')
            descricao = request.form.get('descricao', '').strip()
            cadastro_id = request.form.get('cadastro_id')
            nome_pessoa = request.form.get('nome_pessoa', '').strip()
            numero_recibo = request.form.get('numero_recibo', '').strip()
            observacoes = request.form.get('observacoes', '').strip()
            
            # Validações
            if not descricao:
                flash('Descrição é obrigatória', 'error')
                return redirect(url_for('caixa.editar_movimentacao', movimentacao_id=movimentacao_id))
            
            try:
                valor = float(valor_str)
            except ValueError:
                flash('Valor deve ser um número válido', 'error')
                return redirect(url_for('caixa.editar_movimentacao', movimentacao_id=movimentacao_id))
            
            if valor <= 0:
                flash('Valor deve ser maior que zero', 'error')
                return redirect(url_for('caixa.editar_movimentacao', movimentacao_id=movimentacao_id))
            
            # Converter cadastro_id
            if cadastro_id == '' or cadastro_id is None:
                cadastro_id = None
            else:
                try:
                    cadastro_id = int(cadastro_id)
                except ValueError:
                    cadastro_id = None
            
            # Atualizar movimentação
            cursor.execute('''
                UPDATE movimentacoes_caixa 
                SET tipo = %s, valor = %s, descricao = %s, cadastro_id = %s, 
                    nome_pessoa = %s, numero_recibo = %s, observacoes = %s
                WHERE id = %s
            ''', (tipo, valor, descricao, cadastro_id, nome_pessoa, 
                  numero_recibo, observacoes, movimentacao_id))
            
            linhas_afetadas = cursor.rowcount
            
            if linhas_afetadas == 0:
                flash('Erro ao atualizar movimentação', 'error')
                return redirect(url_for('caixa.editar_movimentacao', movimentacao_id=movimentacao_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Registrar auditoria
            registrar_auditoria(
                session['usuario'], 'UPDATE', 'movimentacoes_caixa', 
                movimentacao_id, str(dados_anteriores), 
                f"Tipo: {tipo}, Valor: {valor}, Descrição: {descricao}"
            )
            
            flash('Movimentação atualizada com sucesso!', 'success')
            return redirect(url_for('caixa.caixa'))
    
    except Exception as e:
        logger.error(f"Erro ao editar movimentação: {e}")
        flash('Erro ao editar movimentação', 'error')
        return redirect(url_for('caixa.caixa'))

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
        # Buscar comprovantes da movimentação
        comprovantes = obter_comprovantes_movimentacao(movimentacao_id)
        
        if not comprovantes:
            flash('Nenhum comprovante encontrado para esta movimentação', 'error')
            return redirect(url_for('caixa.caixa'))
        
        # Se há apenas um comprovante, baixar diretamente
        if len(comprovantes) == 1:
            comp = comprovantes[0]
            
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT arquivo_dados FROM comprovantes_caixa WHERE id = %s', (comp['id'],))
            arquivo_dados = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            
            return send_file(
                io.BytesIO(arquivo_dados),
                as_attachment=True,
                download_name=comp['nome_arquivo'],
                mimetype=comp['tipo_arquivo']
            )
        
        # Se há múltiplos comprovantes, criar ZIP
        import zipfile
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            for comp in comprovantes:
                cursor.execute('SELECT arquivo_dados FROM comprovantes_caixa WHERE id = %s', (comp['id'],))
                arquivo_dados = cursor.fetchone()[0]
                
                zip_file.writestr(comp['nome_arquivo'], arquivo_dados)
            
            cursor.close()
            conn.close()
        
        zip_buffer.seek(0)
        
        return send_file(
            zip_buffer,
            as_attachment=True,
            download_name=f"comprovantes_movimentacao_{movimentacao_id}.zip",
            mimetype='application/zip'
        )
        
    except Exception as e:
        logger.error(f"Erro ao exportar comprovantes: {e}")
        flash('Erro ao exportar comprovantes', 'error')
        return redirect(url_for('caixa.caixa'))
