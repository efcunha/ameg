from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import get_db_connection, registrar_auditoria, usuario_tem_permissao, adicionar_permissao_usuario, obter_permissoes_usuario, remover_permissao_usuario
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2.extras
import logging
import traceback
import re

logger = logging.getLogger(__name__)

usuarios_bp = Blueprint('usuarios', __name__)

def is_admin_user(username):
    """Verifica se o usuário tem privilégios de administrador"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT tipo FROM usuarios WHERE usuario = %s', (username,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            tipo = result[0] if isinstance(result, tuple) else result.get('tipo', 'usuario')
            return tipo == 'admin'
        return username == 'admin'  # Fallback para compatibilidade
    except Exception as e:
        logger.error(f"Erro ao verificar admin: {e}")
        return username == 'admin'  # Fallback para compatibilidade

def validar_senha(senha):
    """Valida se a senha atende aos requisitos de segurança"""
    if len(senha) < 8:
        return False, "Senha deve ter pelo menos 8 caracteres"
    
    if not re.search(r'[A-Z]', senha):
        return False, "Senha deve conter pelo menos uma letra maiúscula"
    
    if not re.search(r'[a-z]', senha):
        return False, "Senha deve conter pelo menos uma letra minúscula"
    
    if not re.search(r'[0-9]', senha):
        return False, "Senha deve conter pelo menos um número"
    
    return True, "Senha válida"

@usuarios_bp.route('/usuarios')
def usuarios():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    if not is_admin_user(session['usuario']):
        flash('Acesso negado! Apenas administradores podem gerenciar usuários.')
        return redirect(url_for('dashboard.dashboard'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, usuario, COALESCE(tipo, \'usuario\') as tipo FROM usuarios ORDER BY usuario')
        usuarios_lista = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Verificar permissão do caixa
        tem_permissao_caixa = session.get('tipo_usuario') == 'admin' or session.get('usuario') == 'admin'
        return render_template('usuarios.html', usuarios=usuarios_lista, tem_permissao_caixa=tem_permissao_caixa)
        
    except Exception as e:
        logger.error(f"Erro ao carregar usuários: {e}")
        flash('Erro ao carregar lista de usuários.')
        # Verificar permissão do caixa
        tem_permissao_caixa = session.get('tipo_usuario') == 'admin' or session.get('usuario') == 'admin'
        return render_template('usuarios.html', usuarios=[], tem_permissao_caixa=tem_permissao_caixa)

@usuarios_bp.route('/criar_usuario', methods=['GET', 'POST'])
def criar_usuario():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    if session['usuario'] != 'admin':
        flash('Acesso negado! Apenas administradores podem criar usuários.')
        return redirect(url_for('dashboard.dashboard'))
    
    if request.method == 'GET':
        return render_template('criar_usuario.html')
    
    # POST
    novo_usuario = request.form['usuario']
    nova_senha = request.form['senha']
    tipo_usuario = request.form.get('tipo', 'usuario')
    
    # Validar senha
    senha_valida, mensagem = validar_senha(nova_senha)
    if not senha_valida:
        flash(f'Erro na senha: {mensagem}')
        return redirect(url_for('usuarios.criar_usuario'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Verificar se usuário já existe
        cursor.execute('SELECT id FROM usuarios WHERE usuario = %s', (novo_usuario,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            flash(f'Usuário "{novo_usuario}" já existe!')
            cursor.close()
            conn.close()
            return redirect(url_for('usuarios.usuarios'))
        
        senha_hash = generate_password_hash(nova_senha)
        
        # No Railway sempre será PostgreSQL
        cursor.execute('INSERT INTO usuarios (usuario, senha, tipo) VALUES (%s, %s, %s) RETURNING id', (novo_usuario, senha_hash, tipo_usuario))
        usuario_id = cursor.fetchone()[0]
        
        # Processar permissões adicionais
        permissoes = request.form.getlist('permissoes')
        
        for permissao in permissoes:
            adicionar_permissao_usuario(usuario_id, permissao)
        
        conn.commit()
        flash('Usuário criado com sucesso!')
    except Exception as e:
        logger.error(f"Erro ao criar usuário: {e}")
        flash(f'Erro ao criar usuário: {str(e)}')
    
    cursor.close()
    conn.close()
    return redirect(url_for('usuarios.usuarios'))

@usuarios_bp.route('/excluir_usuario/<int:usuario_id>')
def excluir_usuario(usuario_id):
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    if not is_admin_user(session['usuario']):
        flash('Acesso negado! Apenas administradores podem excluir usuários.')
        return redirect(url_for('dashboard.dashboard'))
    
    # Proteção especial para admin ID 1
    if usuario_id == 1:
        flash('Erro! O usuário admin principal (ID 1) não pode ser excluído.')
        return redirect(url_for('usuarios.usuarios'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar se é o admin
        cursor.execute('SELECT usuario FROM usuarios WHERE id = %s', (usuario_id,))
        user_data = cursor.fetchone()
        
        if not user_data:
            flash('Usuário não encontrado!')
            cursor.close()
            conn.close()
            return redirect(url_for('usuarios.usuarios'))
        
        username = user_data[0] if isinstance(user_data, tuple) else user_data['usuario']
        
        if username == 'admin':
            flash('Não é possível excluir o usuário admin!')
            cursor.close()
            conn.close()
            return redirect(url_for('usuarios.usuarios'))
        
        # Excluir usuário
        cursor.execute('DELETE FROM usuarios WHERE id = %s', (usuario_id,))
        usuarios_deletados = cursor.rowcount
        
        if usuarios_deletados > 0:
            conn.commit()
            flash(f'Usuário "{username}" excluído com sucesso!')
        else:
            flash('Erro: Usuário não foi excluído.')
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Erro ao excluir usuário: {e}")
        flash(f'Erro ao excluir usuário: {str(e)}')
    
    return redirect(url_for('usuarios.usuarios'))

@usuarios_bp.route('/promover_usuario/<int:usuario_id>')
def promover_usuario(usuario_id):
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    if not is_admin_user(session['usuario']):
        flash('Acesso negado! Apenas administradores podem promover usuários.')
        return redirect(url_for('dashboard.dashboard'))
    
    # Proteção especial para admin ID 1
    if usuario_id == 1:
        flash('O usuário admin principal (ID 1) já possui privilégios máximos.')
        return redirect(url_for('usuarios.usuarios'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar se usuário existe
        cursor.execute('SELECT usuario, tipo FROM usuarios WHERE id = %s', (usuario_id,))
        user_data = cursor.fetchone()
        
        if not user_data:
            flash('Usuário não encontrado!')
            cursor.close()
            conn.close()
            return redirect(url_for('usuarios.usuarios'))
        
        username = user_data[0]
        tipo_atual = user_data[1] if len(user_data) > 1 else 'usuario'
        
        if tipo_atual == 'admin':
            flash(f'Usuário "{username}" já é administrador!')
            cursor.close()
            conn.close()
            return redirect(url_for('usuarios.usuarios'))
        
        # Promover usuário a admin
        cursor.execute('UPDATE usuarios SET tipo = %s WHERE id = %s', ('admin', usuario_id))
        usuarios_atualizados = cursor.rowcount
        
        if usuarios_atualizados > 0:
            conn.commit()
            flash(f'Usuário "{username}" promovido a administrador com sucesso!')
        else:
            flash('Erro: Usuário não foi promovido.')
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Erro ao promover usuário: {e}")
        flash(f'Erro ao promover usuário: {str(e)}')
    
    return redirect(url_for('usuarios.usuarios'))

@usuarios_bp.route('/rebaixar_usuario/<int:usuario_id>')
def rebaixar_usuario(usuario_id):
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    if not is_admin_user(session['usuario']):
        flash('Acesso negado! Apenas administradores podem rebaixar usuários.')
        return redirect(url_for('dashboard.dashboard'))
    
    # Proteção especial para admin ID 1
    if usuario_id == 1:
        flash('Erro! O usuário admin principal (ID 1) não pode ser rebaixado.')
        return redirect(url_for('usuarios.usuarios'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar se usuário existe
        cursor.execute('SELECT usuario, tipo FROM usuarios WHERE id = %s', (usuario_id,))
        user_data = cursor.fetchone()
        
        if not user_data:
            flash('Usuário não encontrado!')
            cursor.close()
            conn.close()
            return redirect(url_for('usuarios.usuarios'))
        
        username = user_data[0]
        tipo_atual = user_data[1] if len(user_data) > 1 else 'usuario'
        
        if username == 'admin':
            flash('Não é possível rebaixar o usuário admin principal!')
            cursor.close()
            conn.close()
            return redirect(url_for('usuarios.usuarios'))
        
        if tipo_atual == 'usuario':
            flash(f'Usuário "{username}" já é usuário comum!')
            cursor.close()
            conn.close()
            return redirect(url_for('usuarios.usuarios'))
        
        # Rebaixar usuário para comum
        cursor.execute('UPDATE usuarios SET tipo = %s WHERE id = %s', ('usuario', usuario_id))
        usuarios_atualizados = cursor.rowcount
        
        if usuarios_atualizados > 0:
            conn.commit()
            flash(f'Usuário "{username}" rebaixado a usuário comum!')
        else:
            flash('Erro: Usuário não foi rebaixado.')
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Erro ao rebaixar usuário: {e}")
        flash(f'Erro ao rebaixar usuário: {str(e)}')
    
    return redirect(url_for('usuarios.usuarios'))

@usuarios_bp.route('/editar_usuario/<int:usuario_id>', methods=['GET', 'POST'])
def editar_usuario(usuario_id):
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    if not is_admin_user(session['usuario']):
        flash('Acesso negado! Apenas administradores podem editar usuários.')
        return redirect(url_for('dashboard.dashboard'))
    
    # Proteção especial para admin ID 1
    if usuario_id == 1:
        # Buscar dados do usuário admin para verificar
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT usuario FROM usuarios WHERE id = 1')
        admin_data = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if admin_data and session['usuario'] != admin_data[0]:
            flash('Acesso negado! Apenas o próprio usuário admin pode alterar sua senha.')
            return redirect(url_for('usuarios.usuarios'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if request.method == 'GET':
            # Buscar dados do usuário
            cursor.execute('SELECT id, usuario, COALESCE(tipo, \'usuario\') as tipo FROM usuarios WHERE id = %s', (usuario_id,))
            user_data = cursor.fetchone()
            
            if not user_data:
                flash('Usuário não encontrado!')
                cursor.close()
                conn.close()
                return redirect(url_for('usuarios.usuarios'))
            
            # Buscar permissões do usuário
            permissoes_usuario = obter_permissoes_usuario(usuario_id)
            
            cursor.close()
            conn.close()
            return render_template('editar_usuario.html', 
                                 usuario=user_data, 
                                 permissoes_usuario=permissoes_usuario)
        
        elif request.method == 'POST':
            # Processar edição
            novo_tipo = request.form.get('tipo', 'usuario')
            nova_senha = request.form.get('nova_senha', '').strip()
            
            # Buscar dados atuais
            cursor.execute('SELECT usuario, tipo FROM usuarios WHERE id = %s', (usuario_id,))
            user_data = cursor.fetchone()
            
            if not user_data:
                flash('Usuário não encontrado!')
                cursor.close()
                conn.close()
                return redirect(url_for('usuarios.usuarios'))
            
            username = user_data[0]
            
            # Proteger admin principal
            if username == 'admin' and novo_tipo != 'admin':
                flash('Não é possível alterar o tipo do usuário admin principal!')
                cursor.close()
                conn.close()
                return redirect(url_for('usuarios.usuarios'))
            
            # Atualizar tipo
            cursor.execute('UPDATE usuarios SET tipo = %s WHERE id = %s', (novo_tipo, usuario_id))
            
            # Processar permissões adicionais
            permissoes_atuais = obter_permissoes_usuario(usuario_id)
            permissoes_novas = request.form.getlist('permissoes')
            
            # Remover permissões que não estão mais selecionadas
            for permissao in permissoes_atuais:
                if permissao not in permissoes_novas:
                    remover_permissao_usuario(usuario_id, permissao)
            
            # Adicionar novas permissões
            for permissao in permissoes_novas:
                if permissao not in permissoes_atuais:
                    adicionar_permissao_usuario(usuario_id, permissao)
            
            # Atualizar senha se fornecida
            if nova_senha:
                senha_hash = generate_password_hash(nova_senha)
                cursor.execute('UPDATE usuarios SET senha = %s WHERE id = %s', (senha_hash, usuario_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            flash(f'Usuário "{username}" atualizado com sucesso!')
            return redirect(url_for('usuarios.usuarios'))
            
    except Exception as e:
        logger.error(f"Erro ao editar usuário: {e}")
        flash(f'Erro ao editar usuário: {str(e)}')
        return redirect(url_for('usuarios.usuarios'))

@usuarios_bp.route('/auditoria')
def auditoria():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    # Verificar se é admin
    if session.get('tipo') != 'admin':
        flash('Acesso negado. Apenas administradores podem acessar a auditoria.')
        return redirect(url_for('dashboard.dashboard'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Parâmetros de filtro
        usuario_filtro = request.args.get('usuario', '')
        acao_filtro = request.args.get('acao', '')
        tabela_filtro = request.args.get('tabela', '')
        data_inicial = request.args.get('data_inicial', '')
        data_final = request.args.get('data_final', '')
        page = int(request.args.get('page', 1))
        per_page = 50
        
        # Construir query com filtros
        where_conditions = []
        params = []
        
        if usuario_filtro:
            where_conditions.append("usuario ILIKE %s")
            params.append(f"%{usuario_filtro}%")
        
        if acao_filtro:
            where_conditions.append("acao = %s")
            params.append(acao_filtro)
        
        if tabela_filtro:
            where_conditions.append("tabela = %s")
            params.append(tabela_filtro)
        
        if data_inicial:
            where_conditions.append("DATE(data_acao) >= %s")
            params.append(data_inicial)
        
        if data_final:
            where_conditions.append("DATE(data_acao) <= %s")
            params.append(data_final)
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # Contar total de registros
        cursor.execute(f"SELECT COUNT(*) as total FROM auditoria {where_clause}", params)
        total_records = cursor.fetchone()['total']
        total_pages = (total_records + per_page - 1) // per_page
        
        # Buscar registros com paginação
        offset = (page - 1) * per_page
        cursor.execute(f"""
            SELECT * FROM auditoria {where_clause}
            ORDER BY data_acao DESC
            LIMIT %s OFFSET %s
        """, params + [per_page, offset])
        
        auditorias = cursor.fetchall()
        
        # Estatísticas
        cursor.execute("SELECT COUNT(*) as total FROM auditoria")
        stats_total = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as hoje FROM auditoria WHERE DATE(data_acao) = CURRENT_DATE")
        stats_hoje = cursor.fetchone()['hoje']
        
        cursor.execute("SELECT COUNT(DISTINCT usuario) as usuarios FROM auditoria WHERE DATE(data_acao) >= CURRENT_DATE - INTERVAL '7 days'")
        stats_usuarios = cursor.fetchone()['usuarios']
        
        cursor.execute("SELECT data_acao FROM auditoria ORDER BY data_acao DESC LIMIT 1")
        ultima_acao = cursor.fetchone()
        stats_ultima = ultima_acao['data_acao'].strftime('%H:%M') if ultima_acao else 'N/A'
        
        stats = {
            'total': stats_total,
            'hoje': stats_hoje,
            'usuarios_ativos': stats_usuarios,
            'ultima_acao': stats_ultima
        }
        
        # Parâmetros para paginação
        query_params = "&".join([f"{k}={v}" for k, v in request.args.items() if k != 'page'])
        
        cursor.close()
        conn.close()
        
        # Verificar permissão do caixa
        tem_permissao_caixa = session.get('tipo_usuario') == 'admin' or session.get('usuario') == 'admin'
        return render_template('auditoria.html', 
                             auditorias=auditorias,
                             stats=stats,
                             page=page,
                             total_pages=total_pages,
                             query_params=query_params,
                             tem_permissao_caixa=tem_permissao_caixa)
        
    except Exception as e:
        logger.error(f"Erro ao carregar auditoria: {e}")
        flash('Erro ao carregar dados de auditoria.')
        return redirect(url_for('dashboard.dashboard'))

@usuarios_bp.route('/admin/reset')
def admin_reset():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    # Verificar se é o admin ID 1
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM usuarios WHERE usuario = %s AND id = 1', (session['usuario'],))
    admin_check = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not admin_check:
        flash('Acesso negado! Apenas o admin principal pode acessar esta funcionalidade.')
        return redirect(url_for('dashboard.dashboard'))
    
    return render_template('admin_reset.html')

@usuarios_bp.route('/admin/reset/execute', methods=['POST'])
def admin_reset_execute():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    # Verificar se é o admin ID 1
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM usuarios WHERE usuario = %s AND id = 1', (session['usuario'],))
    admin_check = cursor.fetchone()
    
    if not admin_check:
        cursor.close()
        conn.close()
        flash('Acesso negado! Apenas o admin principal pode executar o reset.')
        return redirect(url_for('dashboard.dashboard'))
    
    try:
        logger.warning(f"🚨 RESET INICIADO pelo admin ID 1: {session['usuario']}")
        
        # Zerar todas as tabelas (mantém estrutura)
        tabelas_reset = [
            'comprovantes_caixa',
            'movimentacoes_caixa', 
            'historico_notificacoes',
            'dados_saude_pessoa',
            'arquivos_saude',
            'auditoria',
            'cadastros'
        ]
        
        for tabela in tabelas_reset:
            cursor.execute(f'TRUNCATE TABLE {tabela} RESTART IDENTITY CASCADE')
            logger.info(f"✅ Tabela {tabela} resetada")
        
        # Resetar sequences manualmente (garantia)
        sequences_reset = [
            'comprovantes_caixa_id_seq',
            'movimentacoes_caixa_id_seq',
            'historico_notificacoes_id_seq', 
            'dados_saude_pessoa_id_seq',
            'arquivos_saude_id_seq',
            'auditoria_id_seq',
            'cadastros_id_seq'
        ]
        
        for sequence in sequences_reset:
            cursor.execute(f'ALTER SEQUENCE {sequence} RESTART WITH 1')
        
        conn.commit()
        
        # Registrar auditoria do reset
        registrar_auditoria(
            usuario=session['usuario'],
            acao='RESET',
            tabela='SISTEMA',
            dados_novos='Reset completo de todas as tabelas: cadastros, arquivos_saude, auditoria, movimentacoes_caixa, comprovantes_caixa, historico_notificacoes, dados_saude_pessoa (exceto permissoes_usuario)',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        logger.warning(f"✅ RESET CONCLUÍDO pelo admin ID 1: {session['usuario']}")
        flash('Reset executado com sucesso! Todas as tabelas foram zeradas e contadores reiniciados.')
        
    except Exception as e:
        logger.error(f"Erro durante reset: {e}")
        flash(f'Erro durante reset: {str(e)}')
        conn.rollback()
    
    cursor.close()
    conn.close()
    return redirect(url_for('usuarios.admin_reset'))
