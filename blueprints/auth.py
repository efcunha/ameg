from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_from_directory
from database import get_db_connection, registrar_auditoria
import hashlib
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
            
            cursor.execute('SELECT senha FROM usuarios WHERE usuario = %s', (usuario,))
            resultado = cursor.fetchone()
            
            if resultado:
                senha_hash = hashlib.pbkdf2_hmac('sha256', senha.encode('utf-8'), b'salt_', 100000)
                senha_hex = senha_hash.hex()
                
                if resultado[0] == senha_hex:
                    session['usuario'] = usuario
                    
                    # Registrar login na auditoria
                    registrar_auditoria(usuario, 'LOGIN', 'usuarios', None, None, f'Login realizado com sucesso')
                    
                    flash('Login realizado com sucesso!', 'success')
                    cursor.close()
                    conn.close()
                    return redirect(url_for('dashboard.dashboard'))
                else:
                    flash('Usuário ou senha incorretos', 'error')
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
