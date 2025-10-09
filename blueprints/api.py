from flask import Blueprint, jsonify, request, current_app
from functools import wraps
import jwt
import os
from datetime import datetime, timedelta
from .utils import get_db_connection

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token required'}), 401
        
        try:
            token = token.replace('Bearer ', '')
            jwt.decode(token, os.getenv('API_SECRET_KEY', 'default-key'), algorithms=['HS256'])
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    return decorated

@api_bp.route('/token', methods=['POST'])
def generate_token():
    """Gerar token JWT para autenticação"""
    data = request.get_json()
    if not data or data.get('api_key') != os.getenv('API_MASTER_KEY'):
        return jsonify({'error': 'Invalid API key'}), 401
    
    token = jwt.encode({
        'exp': datetime.utcnow() + timedelta(hours=24),
        'iat': datetime.utcnow()
    }, os.getenv('API_SECRET_KEY', 'default-key'), algorithm='HS256')
    
    return jsonify({'token': token})

@api_bp.route('/cadastros', methods=['GET'])
@require_api_key
def get_cadastros():
    """Listar cadastros com paginação"""
    try:
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 100)
        offset = (page - 1) * per_page
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Contar total
        cursor.execute("SELECT COUNT(*) FROM cadastros")
        total = cursor.fetchone()[0]
        
        # Buscar cadastros (sem foto para performance)
        cursor.execute("""
            SELECT id, nome_completo, cpf, telefone, data_cadastro, 
                   endereco, bairro, cep
            FROM cadastros 
            ORDER BY data_cadastro DESC 
            LIMIT %s OFFSET %s
        """, (per_page, offset))
        
        cadastros = []
        for row in cursor.fetchall():
            cadastros.append({
                'id': row[0],
                'nome_completo': row[1],
                'cpf': row[2],
                'telefone': row[3],
                'data_cadastro': row[4].isoformat() if row[4] else None,
                'endereco': row[5],
                'bairro': row[6],
                'cep': row[7]
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'cadastros': cadastros,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/cadastros/<int:cadastro_id>', methods=['GET'])
@require_api_key
def get_cadastro(cadastro_id):
    """Obter cadastro específico"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM cadastros WHERE id = %s", (cadastro_id))
        row = cursor.fetchone()
        
        if not row:
            return jsonify({'error': 'Cadastro não encontrado'}), 404
        
        # Mapear campos (sem foto_base64 para performance)
        columns = [desc[0] for desc in cursor.description]
        cadastro = dict(zip(columns, row))
        
        # Remover foto para API (muito grande)
        cadastro.pop('foto_base64', None)
        
        # Converter datas para ISO
        if cadastro.get('data_cadastro'):
            cadastro['data_cadastro'] = cadastro['data_cadastro'].isoformat()
        if cadastro.get('data_nascimento'):
            cadastro['data_nascimento'] = cadastro['data_nascimento'].isoformat()
        
        cursor.close()
        conn.close()
        
        return jsonify({'cadastro': cadastro})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/stats', methods=['GET'])
@require_api_key
def get_stats():
    """Obter estatísticas do sistema"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total de cadastros
        cursor.execute("SELECT COUNT(*) FROM cadastros")
        total_cadastros = cursor.fetchone()[0]
        
        # Cadastros por mês (últimos 6 meses)
        cursor.execute("""
            SELECT DATE_TRUNC('month', data_cadastro) as mes, COUNT(*) 
            FROM cadastros 
            WHERE data_cadastro >= NOW() - INTERVAL '6 months'
            GROUP BY mes 
            ORDER BY mes DESC
        """)
        cadastros_por_mes = [{'mes': row[0].isoformat(), 'total': row[1]} for row in cursor.fetchall()]
        
        # Estatísticas de saúde
        cursor.execute("SELECT COUNT(*) FROM cadastros WHERE tem_doenca_cronica = 'Sim'")
        com_doenca_cronica = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'total_cadastros': total_cadastros,
            'cadastros_por_mes': cadastros_por_mes,
            'saude': {
                'com_doenca_cronica': com_doenca_cronica,
                'percentual_doenca_cronica': round((com_doenca_cronica / total_cadastros * 100), 2) if total_cadastros > 0 else 0
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check da API (sem autenticação)"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })
