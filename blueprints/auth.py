from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_from_directory
from database import get_db_connection, registrar_auditoria
from werkzeug.security import check_password_hash
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/logo')
def logo():
    """Rota específica para o logo"""
    return send_from_directory('static/img', 'logo-ameg.jpeg')

@auth_bp.route('/')
def index():
    if 'usuario' in session:
        return redirect(url_for('dashboard.dashboard'))
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT senha, tipo FROM usuarios WHERE usuario = %s', (usuario,))
            user = cursor.fetchone()
            
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
                
                flash('Login realizado com sucesso!', 'success')
                cursor.close()
                conn.close()
                return redirect(url_for('dashboard.dashboard'))
            else:
                flash('Usuário ou senha incorretos', 'error')
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erro no login: {e}")
            flash('Erro interno do servidor', 'error')
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    if 'usuario' in session:
        usuario = session['usuario']
        registrar_auditoria(usuario, 'LOGOUT', 'usuarios', None, None, f'Logout realizado')
        session.pop('usuario', None)
        flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('auth.login'))
