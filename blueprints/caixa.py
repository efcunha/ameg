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
