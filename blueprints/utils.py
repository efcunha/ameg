# Utilitários compartilhados entre blueprints

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}

# Limites dos campos conforme definido na tabela do banco
FIELD_LIMITS = {
    'nome_completo': 255,
    'numero': 10,
    'bairro': 100,
    'cep': 10,
    'telefone': 20,
    'titulo_eleitor': 20,
    'cidade_titulo': 100,
    'cpf': 14,
    'rg': 20,
    'nis': 20,
    'estado_civil': 30,
    'escolaridade': 100,
    'profissao': 100,
    'nome_companheiro': 255,
    'cpf_companheiro': 14,
    'rg_companheiro': 20,
    'escolaridade_companheiro': 100,
    'profissao_companheiro': 100,
    'titulo_companheiro': 20,
    'cidade_titulo_companheiro': 100,
    'nis_companheiro': 20,
    'tipo_trabalho': 100,
    'casa_tipo': 50,
    'casa_material': 50,
    'energia': 10,
    'lixo': 10,
    'agua': 10,
    'esgoto': 10,
    'tem_doenca_cronica': 10,
    'usa_medicamento_continuo': 10,
    'tem_doenca_mental': 10,
    'tem_deficiencia': 10,
    'precisa_cuidados_especiais': 10,
    'atua_ponto_fixo': 10,
    'trabalho_continuo_temporada': 20,
    'sofreu_acidente_trabalho': 10,
    'trabalho_incomoda_calor': 10,
    'trabalho_incomoda_barulho': 10,
    'trabalho_incomoda_seguranca': 10,
    'trabalho_incomoda_banheiros': 10,
    'trabalho_incomoda_outro': 10,
    'acesso_banheiro_agua': 10,
    'possui_autorizacao_municipal': 10,
    'problemas_fiscalizacao_policia': 10,
    'estrutura_barraca': 10,
    'estrutura_carrinho': 10,
    'estrutura_mesa': 10,
    'estrutura_outro': 10,
    'necessita_energia_eletrica': 10,
    'utiliza_gas_cozinha': 10,
    'usa_veiculo_proprio': 10,
    'fonte_renda_trabalho_ambulante': 10,
    'fonte_renda_aposentadoria': 10,
    'fonte_renda_outro_trabalho': 10,
    'fonte_renda_beneficio_social': 10,
    'fonte_renda_outro': 10
}

def validate_field_lengths(form_data):
    """Valida se os campos não excedem os limites da tabela"""
    errors = []
    
    for field_name, max_length in FIELD_LIMITS.items():
        if field_name in form_data:
            value = str(form_data[field_name]).strip()
            if len(value) > max_length:
                field_display = field_name.replace('_', ' ').title()
                errors.append(f"{field_display}: máximo {max_length} caracteres (atual: {len(value)})")
    
    return errors

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validar_senha(senha):
    """Valida se a senha atende aos critérios de segurança"""
    if len(senha) < 8:
        return False, "A senha deve ter pelo menos 8 caracteres"
    
    if not any(c.isupper() for c in senha):
        return False, "A senha deve conter pelo menos uma letra maiúscula"
    
    if not any(c.islower() for c in senha):
        return False, "A senha deve conter pelo menos uma letra minúscula"
    
    if not any(c.isdigit() for c in senha):
        return False, "A senha deve conter pelo menos um número"
    
    return True, "Senha válida"

def login_required(f):
    """Decorador para verificar se usuário está logado"""
    from functools import wraps
    from flask import session, redirect, url_for
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def tem_permissao_caixa(usuario,):
    """Verifica se o usuário tem permissão para acessar o caixa"""
    if not usuario:
        return False
    
    try:
        from database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar se é admin
        cursor.execute('SELECT tipo_usuario FROM usuarios WHERE usuario = %s', (usuario,))
        user_data = cursor.fetchone()
        
        if user_data and user_data[0] == 'admin':
            cursor.close()
            conn.close()
            return True
        
        # Verificar permissões específicas
        cursor.execute('''
            SELECT p.permissao 
            FROM permissoes_usuario p 
            JOIN usuarios u ON p.usuario_id = u.id 
            WHERE u.usuario = %s AND p.permissao = 'caixa'
        ''', (usuario,))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return result is not None
        
    except Exception as e:
        print(f"Erro ao verificar permissão caixa: {e}")
        return False

def is_admin_id_1(usuario,):
    """Verifica se o usuário é o admin ID 1"""
    if not usuario:
        return False
    
    try:
        from database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM usuarios WHERE usuario = %s AND id = 1', (usuario,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result is not None
    except:
        return False
