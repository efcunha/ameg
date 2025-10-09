from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_from_directory, current_app
from database import get_db_connection, registrar_auditoria
from werkzeug.security import check_password_hash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

# Rate limiter para este blueprint
limiter = Limiter(key_func=get_remote_address)

@auth_bp.route('/logo')
def logo():
    """Rota específica para o logo"""
    return send_from_directory('static/img', 'logo-ameg.jpeg')

@auth_bp.route('/')
def login():
    if 'usuario' in session:
        return redirect(url_for('dashboard.dashboard'))
    
    # Limpar mensagens flash antigas na tela de login
    session.pop('_flashes', None)
    
    return render_template('login.html')

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")  # Máximo 5 tentativas por minuto
def fazer_login():
    usuario = request.form['usuario']
    senha = request.form['senha']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # No Railway sempre será PostgreSQL
    cursor.execute('SELECT senha, tipo FROM usuarios WHERE usuario = %s', (usuario))
    
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if user and check_password_hash(user[0], senha):
        session['usuario'] = usuario
        session['tipo'] = user[1]  # Definir o tipo na sessão
        
        # Registrar auditoria de login
        registrar_auditoria(
            usuario=usuario,
            acao='LOGIN',
            tabela='usuarios',
            dados_novos=f"Login realizado com sucesso",
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return redirect(url_for('dashboard.dashboard'))
    else:
        flash('Usuário ou senha incorretos!')
        return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('auth.login'))
