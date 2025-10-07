from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import get_db_connection, registrar_auditoria, usuario_tem_permissao, adicionar_permissao_usuario, obter_permissoes_usuario, remover_permissao_usuario
import hashlib
import logging

logger = logging.getLogger(__name__)

usuarios_bp = Blueprint('usuarios', __name__)

@usuarios_bp.route('/usuarios')
def usuarios():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, usuario, tipo FROM usuarios ORDER BY usuario')
        usuarios_lista = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('usuarios.html', usuarios=usuarios_lista)
    
    except Exception as e:
        logger.error(f"Erro ao listar usuários: {e}")
        flash('Erro ao carregar usuários', 'error')
        return redirect(url_for('dashboard.dashboard'))

@usuarios_bp.route('/criar_usuario', methods=['GET', 'POST'])
def criar_usuario():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        try:
            usuario = request.form['usuario'].strip()
            senha = request.form['senha']
            tipo = request.form['tipo']
            
            # Validações
            if len(senha) < 8:
                flash('Senha deve ter pelo menos 8 caracteres', 'error')
                return render_template('criar_usuario.html')
            
            # Hash da senha
            senha_hash = hashlib.pbkdf2_hmac('sha256', senha.encode('utf-8'), b'salt_', 100000)
            senha_hex = senha_hash.hex()
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Verificar se usuário já existe
            cursor.execute('SELECT id FROM usuarios WHERE usuario = %s', (usuario,))
            if cursor.fetchone():
                flash('Usuário já existe', 'error')
                cursor.close()
                conn.close()
                return render_template('criar_usuario.html')
            
            # Inserir usuário
            cursor.execute('''
                INSERT INTO usuarios (usuario, senha, tipo) 
                VALUES (%s, %s, %s) RETURNING id
            ''', (usuario, senha_hex, tipo))
            
            usuario_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
            
            # Registrar auditoria
            registrar_auditoria(
                session['usuario'], 'INSERT', 'usuarios', usuario_id,
                None, f"Usuário criado: {usuario} (tipo: {tipo})"
            )
            
            flash('Usuário criado com sucesso!', 'success')
            return redirect(url_for('usuarios.usuarios'))
            
        except Exception as e:
            logger.error(f"Erro ao criar usuário: {e}")
            flash('Erro ao criar usuário', 'error')
    
    return render_template('criar_usuario.html')

@usuarios_bp.route('/editar_usuario/<int:usuario_id>', methods=['GET', 'POST'])
def editar_usuario(usuario_id):
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if request.method == 'GET':
            # Buscar dados do usuário
            cursor.execute('SELECT id, usuario, tipo FROM usuarios WHERE id = %s', (usuario_id,))
            usuario_data = cursor.fetchone()
            
            if not usuario_data:
                flash('Usuário não encontrado', 'error')
                return redirect(url_for('usuarios.usuarios'))
            
            # Buscar permissões
            permissoes = obter_permissoes_usuario(usuario_data[1])
            
            cursor.close()
            conn.close()
            
            return render_template('editar_usuario.html', 
                                 usuario_data=usuario_data, 
                                 permissoes=permissoes)
        
        elif request.method == 'POST':
            # Buscar dados atuais
            cursor.execute('SELECT usuario, tipo FROM usuarios WHERE id = %s', (usuario_id,))
            dados_anteriores = cursor.fetchone()
            
            if not dados_anteriores:
                flash('Usuário não encontrado', 'error')
                return redirect(url_for('usuarios.usuarios'))
            
            # Proteção especial para admin ID 1
            if usuario_id == 1 and session['usuario'] != dados_anteriores[0]:
                flash('Apenas o próprio admin pode modificar sua conta', 'error')
                return redirect(url_for('usuarios.usuarios'))
            
            # Atualizar dados básicos se fornecidos
            if 'tipo' in request.form and dados_anteriores[1] != request.form['tipo']:
                if usuario_id == 1:
                    flash('Não é possível alterar o tipo do admin principal', 'error')
                else:
                    cursor.execute('UPDATE usuarios SET tipo = %s WHERE id = %s', 
                                 (request.form['tipo'], usuario_id))
            
            # Atualizar senha se fornecida
            if 'nova_senha' in request.form and request.form['nova_senha']:
                nova_senha = request.form['nova_senha']
                if len(nova_senha) >= 8:
                    senha_hash = hashlib.pbkdf2_hmac('sha256', nova_senha.encode('utf-8'), b'salt_', 100000)
                    senha_hex = senha_hash.hex()
                    cursor.execute('UPDATE usuarios SET senha = %s WHERE id = %s', 
                                 (senha_hex, usuario_id))
                else:
                    flash('Nova senha deve ter pelo menos 8 caracteres', 'error')
            
            # Gerenciar permissões
            if 'permissoes' in request.form:
                permissoes_atuais = obter_permissoes_usuario(dados_anteriores[0])
                permissoes_novas = request.form.getlist('permissoes')
                
                # Remover permissões que não estão mais selecionadas
                for perm in permissoes_atuais:
                    if perm not in permissoes_novas:
                        remover_permissao_usuario(dados_anteriores[0], perm)
                
                # Adicionar novas permissões
                for perm in permissoes_novas:
                    if perm not in permissoes_atuais:
                        adicionar_permissao_usuario(dados_anteriores[0], perm)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Registrar auditoria
            registrar_auditoria(
                session['usuario'], 'UPDATE', 'usuarios', usuario_id,
                str(dados_anteriores), f"Usuário atualizado: {dados_anteriores[0]}"
            )
            
            flash('Usuário atualizado com sucesso!', 'success')
            return redirect(url_for('usuarios.usuarios'))
    
    except Exception as e:
        logger.error(f"Erro ao editar usuário: {e}")
        flash('Erro ao editar usuário', 'error')
        return redirect(url_for('usuarios.usuarios'))

@usuarios_bp.route('/excluir_usuario/<int:usuario_id>')
def excluir_usuario(usuario_id):
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    # Proteção: não permitir exclusão do admin ID 1
    if usuario_id == 1:
        flash('Não é possível excluir o usuário admin principal', 'error')
        return redirect(url_for('usuarios.usuarios'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Buscar dados do usuário para auditoria
        cursor.execute('SELECT usuario, tipo FROM usuarios WHERE id = %s', (usuario_id,))
        usuario_data = cursor.fetchone()
        
        if not usuario_data:
            flash('Usuário não encontrado', 'error')
            return redirect(url_for('usuarios.usuarios'))
        
        # Excluir usuário
        cursor.execute('DELETE FROM usuarios WHERE id = %s', (usuario_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        # Registrar auditoria
        registrar_auditoria(
            session['usuario'], 'DELETE', 'usuarios', usuario_id,
            str(usuario_data), f"Usuário excluído: {usuario_data[0]}"
        )
        
        flash('Usuário excluído com sucesso!', 'success')
        
    except Exception as e:
        logger.error(f"Erro ao excluir usuário: {e}")
        flash('Erro ao excluir usuário', 'error')
    
    return redirect(url_for('usuarios.usuarios'))

@usuarios_bp.route('/promover_usuario/<int:usuario_id>')
def promover_usuario(usuario_id):
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    # Verificar se é admin
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT tipo FROM usuarios WHERE usuario = %s', (session['usuario'],))
    user_type = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not user_type or user_type[0] != 'admin':
        flash('Acesso negado! Apenas administradores podem promover usuários.', 'error')
        return redirect(url_for('dashboard.dashboard'))
    
    # Proteção especial para admin ID 1
    if usuario_id == 1:
        flash('O usuário admin principal (ID 1) já possui privilégios máximos.', 'warning')
        return redirect(url_for('usuarios.usuarios'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar se usuário existe
        cursor.execute('SELECT usuario, tipo FROM usuarios WHERE id = %s', (usuario_id,))
        user_data = cursor.fetchone()
        
        if not user_data:
            flash('Usuário não encontrado!', 'error')
            cursor.close()
            conn.close()
            return redirect(url_for('usuarios.usuarios'))
        
        username = user_data[0]
        tipo_atual = user_data[1] if len(user_data) > 1 else 'usuario'
        
        if tipo_atual == 'admin':
            flash(f'Usuário "{username}" já é administrador!', 'warning')
            cursor.close()
            conn.close()
            return redirect(url_for('usuarios.usuarios'))
        
        # Promover usuário a admin
        cursor.execute('UPDATE usuarios SET tipo = %s WHERE id = %s', ('admin', usuario_id))
        conn.commit()
        
        flash(f'Usuário "{username}" promovido a administrador com sucesso!', 'success')
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Erro ao promover usuário ID {usuario_id}: {e}")
        flash(f'Erro ao promover usuário: {str(e)}', 'error')
    
    return redirect(url_for('usuarios.usuarios'))

@usuarios_bp.route('/rebaixar_usuario/<int:usuario_id>')
def rebaixar_usuario(usuario_id):
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    # Verificar se é admin
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT tipo FROM usuarios WHERE usuario = %s', (session['usuario'],))
    user_type = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not user_type or user_type[0] != 'admin':
        flash('Acesso negado! Apenas administradores podem rebaixar usuários.', 'error')
        return redirect(url_for('dashboard.dashboard'))
    
    # Proteção especial para admin ID 1
    if usuario_id == 1:
        flash('Erro! O usuário admin principal (ID 1) não pode ser rebaixado.', 'error')
        return redirect(url_for('usuarios.usuarios'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar se usuário existe
        cursor.execute('SELECT usuario, tipo FROM usuarios WHERE id = %s', (usuario_id,))
        user_data = cursor.fetchone()
        
        if not user_data:
            flash('Usuário não encontrado!', 'error')
            cursor.close()
            conn.close()
            return redirect(url_for('usuarios.usuarios'))
        
        username = user_data[0]
        tipo_atual = user_data[1] if len(user_data) > 1 else 'usuario'
        
        if username == 'admin':
            flash('Não é possível rebaixar o usuário admin principal!', 'error')
            cursor.close()
            conn.close()
            return redirect(url_for('usuarios.usuarios'))
        
        if tipo_atual == 'usuario':
            flash(f'Usuário "{username}" já é usuário comum!', 'warning')
            cursor.close()
            conn.close()
            return redirect(url_for('usuarios.usuarios'))
        
        # Rebaixar usuário
        cursor.execute('UPDATE usuarios SET tipo = %s WHERE id = %s', ('usuario', usuario_id))
        conn.commit()
        
        flash(f'Usuário "{username}" rebaixado para usuário comum com sucesso!', 'success')
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Erro ao rebaixar usuário ID {usuario_id}: {e}")
        flash(f'Erro ao rebaixar usuário: {str(e)}', 'error')
    
    return redirect(url_for('usuarios.usuarios'))

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
        flash('Acesso negado! Apenas o admin principal pode acessar esta funcionalidade.', 'error')
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
        flash('Acesso negado! Apenas o admin principal pode executar o reset.', 'error')
        return redirect(url_for('dashboard.dashboard'))
    
    try:
        logger.warning(f"🚨 RESET INICIADO pelo admin ID 1: {session['usuario']}")
        
        # Zerar tabelas (mantém estrutura)
        cursor.execute('TRUNCATE TABLE arquivos_saude RESTART IDENTITY CASCADE')
        cursor.execute('TRUNCATE TABLE auditoria RESTART IDENTITY CASCADE')
        cursor.execute('TRUNCATE TABLE cadastros RESTART IDENTITY CASCADE')
        
        # Resetar sequences manualmente (garantia)
        cursor.execute('ALTER SEQUENCE arquivos_saude_id_seq RESTART WITH 1')
        cursor.execute('ALTER SEQUENCE auditoria_id_seq RESTART WITH 1')
        cursor.execute('ALTER SEQUENCE cadastros_id_seq RESTART WITH 1')
        
        conn.commit()
        
        # Registrar auditoria do reset
        registrar_auditoria(
            usuario=session['usuario'],
            acao='RESET',
            tabela='SISTEMA',
            dados_novos='Reset completo das tabelas: cadastros, arquivos_saude, auditoria',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        logger.warning(f"✅ RESET CONCLUÍDO pelo admin ID 1: {session['usuario']}")
        flash('Reset executado com sucesso! Todas as tabelas foram zeradas e contadores reiniciados.', 'success')
        
    except Exception as e:
        logger.error(f"❌ Erro durante reset: {e}")
        flash(f'Erro durante reset: {str(e)}', 'error')
        conn.rollback()
    
    cursor.close()
    conn.close()
    return redirect(url_for('usuarios.admin_reset'))
