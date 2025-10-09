from flask import Blueprint, render_template, session, redirect, url_for
from database import get_db_connection, usuario_tem_permissao
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__)

# Cache simples em memória para estatísticas
stats_cache = {
    'data': None,
    'timestamp': None,
    'ttl': 300  # 5 minutos
}

def get_cached_stats():
    """Retorna estatísticas do cache ou busca no banco se expirado"""
    now = datetime.now()
    
    # Verificar se cache é válido
    if (stats_cache['data'] is not None and 
        stats_cache['timestamp'] is not None and
        (now - stats_cache['timestamp']).seconds < stats_cache['ttl']):
        return stats_cache['data']
    
    # Cache expirado, buscar dados atualizados
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Contar registros otimizado
        cursor.execute('SELECT COUNT(*) FROM cadastros')
        total_cadastros = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM arquivos_saude')
        total_arquivos = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM usuarios WHERE tipo = %s', ('admin',))
        total_admins = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        # Atualizar cache
        stats_cache['data'] = {
            'total': total_cadastros,
            'arquivos': total_arquivos,
            'admins': total_admins
        }
        stats_cache['timestamp'] = now
        
        return stats_cache['data']
        
    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas: {e}")
        return {'total': 0, 'arquivos': 0, 'admins': 0}

def invalidate_stats_cache():
    """Invalida o cache de estatísticas"""
    stats_cache['data'] = None
    stats_cache['timestamp'] = None

@dashboard_bp.route('/dashboard')
def dashboard():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    # Usar cache para estatísticas
    stats = get_cached_stats()
    
    # Verificar permissão de caixa
    tem_permissao_caixa = usuario_tem_permissao(session['usuario'], 'caixa')
    
    # Buscar últimos cadastros (não cachear pois muda frequentemente)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, nome_completo, telefone, bairro, data_cadastro FROM cadastros ORDER BY data_cadastro DESC LIMIT 5')
    ultimos = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('dashboard.html', 
                         total=stats['total'], 
                         ultimos=ultimos,
                         )

@dashboard_bp.route('/api/stats')
def api_stats():
    if 'usuario' not in session:
        return {"error": "Não autorizado"}, 401
    
    try:
        # Usar cache para estatísticas
        stats = get_cached_stats()
        
        return {
            "cadastros": stats['total'],
            "arquivos": stats['arquivos'],
            "auditoria": stats.get('auditoria', 0)  # Fallback para compatibilidade
        }
        
    except Exception as e:
        logger.error(f"Erro na API stats: {e}")
        return {"error": str(e)}, 500
