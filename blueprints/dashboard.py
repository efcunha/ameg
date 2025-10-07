from flask import Blueprint, render_template, session, redirect, url_for
from database import get_db_connection, usuario_tem_permissao
import time
import logging

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__)

# Cache simples para estatísticas
def get_cached_stats():
    """Função local para obter estatísticas"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM cadastros')
        total_cadastros = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM arquivos_saude')
        total_arquivos = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM usuarios WHERE tipo = %s', ('admin',))
        total_admins = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return {
            'total': total_cadastros,
            'arquivos': total_arquivos,
            'admins': total_admins
        }
    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas: {e}")
        return {'total': 0, 'arquivos': 0, 'admins': 0}
stats_cache = {'data': None, 'timestamp': None}

def get_cached_stats():
    """Obtém estatísticas com cache de 5 minutos"""
    current_time = time.time()
    
    if (stats_cache['data'] is None or 
        stats_cache['timestamp'] is None or 
        current_time - stats_cache['timestamp'] > 300):  # 5 minutos
        
        logger.info("📊 Cache expirado, buscando novas estatísticas...")
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Total de cadastros
            cursor.execute('SELECT COUNT(*) FROM cadastros')
            total = cursor.fetchone()[0]
            
            # Cadastros por bairro (top 5)
            cursor.execute('''
                SELECT bairro, COUNT(*) as total 
                FROM cadastros 
                WHERE bairro IS NOT NULL AND bairro != '' 
                GROUP BY bairro 
                ORDER BY total DESC 
                LIMIT 5
            ''')
            por_bairro = cursor.fetchall()
            
            # Estatísticas de saúde
            cursor.execute('''
                SELECT 
                    COUNT(CASE WHEN doencas_cronicas = 'sim' THEN 1 END) as com_doenca,
                    COUNT(CASE WHEN tem_deficiencia = 'sim' THEN 1 END) as com_deficiencia,
                    COUNT(CASE WHEN medicamento_continuo = 'sim' THEN 1 END) as usa_medicamento
                FROM cadastros
            ''')
            saude = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            stats_cache['data'] = {
                'total': total,
                'por_bairro': por_bairro,
                'saude': {
                    'com_doenca': saude[0],
                    'com_deficiencia': saude[1], 
                    'usa_medicamento': saude[2]
                }
            }
            stats_cache['timestamp'] = current_time
            logger.info("✅ Estatísticas atualizadas no cache")
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {'total': 0, 'por_bairro': [], 'saude': {'com_doenca': 0, 'com_deficiencia': 0, 'usa_medicamento': 0}}
    
    return stats_cache['data']

@dashboard_bp.route('/dashboard')
def dashboard():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    try:
        # Obter estatísticas (com cache)
        stats = get_cached_stats()
        
        # Verificar permissão de caixa
        tem_permissao_caixa = usuario_tem_permissao(session['usuario'], 'caixa')
        
        # Buscar últimos cadastros (não cachear pois muda frequentemente)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT nome_completo, bairro, data_cadastro 
            FROM cadastros 
            ORDER BY data_cadastro DESC 
            LIMIT 5
        ''')
        ultimos = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return render_template('dashboard.html', 
                            total=stats['total'], 
                            ultimos=ultimos,
                            tem_permissao_caixa=tem_permissao_caixa)
    
    except Exception as e:
        logger.error(f"Erro no dashboard: {e}")
        return render_template('dashboard.html', total=0, ultimos=[])

@dashboard_bp.route('/api/stats')
def api_stats():
    if 'usuario' not in session:
        return {"error": "Não autorizado"}, 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM cadastros')
        total_cadastros = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM arquivos_saude')
        total_arquivos = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return {
            "cadastros": total_cadastros,
            "arquivos": total_arquivos,
            "auditoria": 0
        }
        
    except Exception as e:
        logger.error(f"Erro na API stats: {e}")
        return {"error": str(e)}, 500
