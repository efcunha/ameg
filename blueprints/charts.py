from flask import Blueprint, jsonify, render_template, session, redirect, url_for
from database import get_db_connection
from datetime import datetime, timedelta
import logging

charts_bp = Blueprint('charts', __name__)
logger = logging.getLogger(__name__)

def login_required(f):
    """Decorator para verificar se usuário está logado"""
    def decorated_function(*args, **kwargs):
        logger.info(f"🔐 Verificando login para {f.__name__}")
        logger.info(f"📋 Session keys: {list(session.keys())}")
        logger.info(f"👤 Usuario na session: {session.get('usuario', 'NONE')}")
        
        if 'usuario' not in session:
            logger.warning("❌ Usuário não logado, redirecionando para login")
            return redirect(url_for('auth.login'))
        
        logger.info(f"✅ Usuário logado: {session.get('usuario', 'unknown')}")
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def execute_query(query):
    """Executa query e retorna resultados"""
    logger.info(f"🔍 Executando query: {query[:100]}...")
    try:
        conn = get_db_connection()
        logger.info("✅ Conexão com banco estabelecida")
        
        cursor = conn.cursor()
        logger.info("✅ Cursor criado")
        
        cursor.execute(query)
        logger.info("✅ Query executada com sucesso")
        
        results = cursor.fetchall()
        logger.info(f"📊 Resultados obtidos: {len(results)} registros")
        
        # Converter para lista de dicionários
        columns = [desc[0] for desc in cursor.description]
        logger.info(f"📋 Colunas: {columns}")
        
        data = [dict(zip(columns, row)) for row in results]
        logger.info(f"📦 Dados convertidos: {data[:3] if data else 'Nenhum dado'}")
        
        cursor.close()
        conn.close()
        logger.info("🔒 Conexão fechada")
        
        return data
    except Exception as e:
        logger.error(f"❌ Erro na query: {e}")
        logger.error(f"📝 Query que falhou: {query}")
        return []

@charts_bp.route('/charts')
@login_required
def charts_page():
    """Página principal dos gráficos"""
    logger.info("🎯 ACESSANDO PÁGINA DE GRÁFICOS")
    logger.info(f"👤 Usuário: {session.get('usuario', 'unknown')}")
    logger.info(f"🔑 Tipo: {session.get('tipo', 'unknown')}")
    logger.info(f"📋 Session completa: {dict(session)}")
    
    try:
        logger.info("🎨 Renderizando template charts.html")
        return render_template('charts.html')
    except Exception as e:
        logger.error(f"❌ Erro ao renderizar template: {e}")
        return f"Erro ao carregar página: {e}", 500

@charts_bp.route('/api/charts/demografia')
@login_required
def demografia_data():
    """Dados demográficos para gráficos"""
    logger.info("📊 INICIANDO API DEMOGRAFIA")
    try:
        # Faixa etária
        logger.info("🎂 Executando query de faixa etária...")
        idade_query = """
        SELECT 
            CASE 
                WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, TO_DATE(data_nascimento, 'YYYY-MM-DD'))) < 18 THEN 'Menor 18'
                WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, TO_DATE(data_nascimento, 'YYYY-MM-DD'))) < 30 THEN '18-29'
                WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, TO_DATE(data_nascimento, 'YYYY-MM-DD'))) < 50 THEN '30-49'
                ELSE '50+'
            END as faixa,
            COUNT(*) as total
        FROM cadastros 
        WHERE data_nascimento IS NOT NULL AND data_nascimento != ''
        GROUP BY faixa
        ORDER BY faixa
        """
        idade_data = execute_query(idade_query)
        logger.info(f"✅ Dados de idade obtidos: {len(idade_data)} registros")
        
        # Bairros
        logger.info("🏘️ Executando query de bairros...")
        bairro_query = """
        SELECT bairro, COUNT(*) as total
        FROM cadastros 
        WHERE bairro IS NOT NULL AND bairro != ''
        GROUP BY bairro
        ORDER BY total DESC
        LIMIT 10
        """
        bairros_data = execute_query(bairro_query)
        logger.info(f"✅ Dados de bairros obtidos: {len(bairros_data)} registros")
        
        # Evolução mensal
        logger.info("📈 Executando query de evolução mensal...")
        evolucao_query = """
        SELECT 
            TO_CHAR(TO_DATE(data_cadastro, 'YYYY-MM-DD'), 'YYYY-MM') as mes,
            COUNT(*) as total
        FROM cadastros 
        WHERE data_cadastro IS NOT NULL
        GROUP BY mes
        ORDER BY mes DESC
        LIMIT 12
        """
        evolucao_data = execute_query(evolucao_query)
        logger.info(f"✅ Dados de evolução obtidos: {len(evolucao_data)} registros")
        
        result = {
            'idade': idade_data,
            'bairros': bairros_data,
            'evolucao': evolucao_data
        }
        logger.info(f"📦 Retornando dados demografia: {result}")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ ERRO DEMOGRAFIA: {e}")
        logger.error(f"📍 Traceback completo:", exc_info=True)
        return jsonify({'error': str(e)}), 500

@charts_bp.route('/api/charts/saude')
@login_required
def saude_data():
    """Dados de saúde para gráficos"""
    logger.info("🏥 INICIANDO API SAÚDE")
    try:
        # Doenças crônicas
        logger.info("💊 Executando query de doenças crônicas...")
        doencas_query = """
        SELECT doencas_cronicas, COUNT(*) as total
        FROM cadastros 
        WHERE tem_doenca_cronica = true AND doencas_cronicas IS NOT NULL AND doencas_cronicas != ''
        GROUP BY doencas_cronicas
        ORDER BY total DESC
        LIMIT 10
        """
        doencas_data = execute_query(doencas_query)
        logger.info(f"✅ Dados de doenças obtidos: {len(doencas_data)} registros")
        
        # Medicamentos
        logger.info("💉 Executando query de medicamentos...")
        medicamentos_query = """
        SELECT medicamentos_uso, COUNT(*) as total
        FROM cadastros 
        WHERE medicamentos_uso IS NOT NULL AND medicamentos_uso != ''
        GROUP BY medicamentos_uso
        ORDER BY total DESC
        LIMIT 10
        """
        medicamentos_data = execute_query(medicamentos_query)
        logger.info(f"✅ Dados de medicamentos obtidos: {len(medicamentos_data)} registros")
        
        # Deficiências
        logger.info("♿ Executando query de deficiências...")
        deficiencias_query = """
        SELECT deficiencia_tipo, COUNT(*) as total
        FROM cadastros 
        WHERE tem_deficiencia = true AND deficiencia_tipo IS NOT NULL AND deficiencia_tipo != ''
        GROUP BY deficiencia_tipo
        ORDER BY total DESC
        """
        deficiencias_data = execute_query(deficiencias_query)
        logger.info(f"✅ Dados de deficiências obtidos: {len(deficiencias_data)} registros")
        
        result = {
            'doencas': doencas_data,
            'medicamentos': medicamentos_data,
            'deficiencias': deficiencias_data
        }
        logger.info(f"📦 Retornando dados saúde: {result}")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ ERRO SAÚDE: {e}")
        logger.error(f"📍 Traceback completo:", exc_info=True)
        return jsonify({'error': str(e)}), 500

@charts_bp.route('/api/charts/socioeconomico')
@login_required
def socioeconomico_data():
    """Dados socioeconômicos para gráficos"""
    logger.info("💰 INICIANDO API SOCIOECONÔMICO")
    try:
        # Renda familiar
        logger.info("💵 Executando query de renda familiar...")
        renda_query = """
        SELECT 
            CASE 
                WHEN CAST(renda_familiar AS FLOAT) < 1000 THEN 'Até R$ 1.000'
                WHEN CAST(renda_familiar AS FLOAT) < 2000 THEN 'R$ 1.000 - R$ 2.000'
                WHEN CAST(renda_familiar AS FLOAT) < 3000 THEN 'R$ 2.000 - R$ 3.000'
                ELSE 'Acima R$ 3.000'
            END as faixa_renda,
            COUNT(*) as total
        FROM cadastros 
        WHERE renda_familiar IS NOT NULL AND renda_familiar != '' AND renda_familiar ~ '^[0-9.]+$'
        GROUP BY faixa_renda
        ORDER BY total DESC
        """
        renda_data = execute_query(renda_query)
        logger.info(f"✅ Dados de renda obtidos: {len(renda_data)} registros")
        
        # Tipos de moradia
        logger.info("🏠 Executando query de tipos de moradia...")
        moradia_query = """
        SELECT casa_tipo, COUNT(*) as total
        FROM cadastros 
        WHERE casa_tipo IS NOT NULL AND casa_tipo != ''
        GROUP BY casa_tipo
        ORDER BY total DESC
        """
        moradia_data = execute_query(moradia_query)
        logger.info(f"✅ Dados de moradia obtidos: {len(moradia_data)} registros")
        
        # Benefícios sociais
        logger.info("🎁 Executando query de benefícios sociais...")
        beneficios_query = """
        SELECT beneficios_sociais, COUNT(*) as total
        FROM cadastros 
        WHERE beneficios_sociais IS NOT NULL AND beneficios_sociais != ''
        GROUP BY beneficios_sociais
        ORDER BY total DESC
        """
        beneficios_data = execute_query(beneficios_query)
        logger.info(f"✅ Dados de benefícios obtidos: {len(beneficios_data)} registros")
        
        result = {
            'renda': renda_data,
            'moradia': moradia_data,
            'beneficios': beneficios_data
        }
        logger.info(f"📦 Retornando dados socioeconômico: {result}")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ ERRO SOCIOECONÔMICO: {e}")
        logger.error(f"📍 Traceback completo:", exc_info=True)
        return jsonify({'error': str(e)}), 500

@charts_bp.route('/api/charts/trabalho')
@login_required
def trabalho_data():
    """Dados de trabalho para gráficos"""
    logger.info("💼 INICIANDO API TRABALHO")
    try:
        # Tipos de trabalho
        logger.info("🔨 Executando query de tipos de trabalho...")
        trabalho_query = """
        SELECT tipo_trabalho, COUNT(*) as total
        FROM cadastros 
        WHERE tipo_trabalho IS NOT NULL AND tipo_trabalho != ''
        GROUP BY tipo_trabalho
        ORDER BY total DESC
        """
        tipos_data = execute_query(trabalho_query)
        logger.info(f"✅ Dados de tipos de trabalho obtidos: {len(tipos_data)} registros")
        
        # Local de trabalho
        logger.info("📍 Executando query de locais de trabalho...")
        local_query = """
        SELECT local_trabalho, COUNT(*) as total
        FROM cadastros 
        WHERE local_trabalho IS NOT NULL AND local_trabalho != ''
        GROUP BY local_trabalho
        ORDER BY total DESC
        LIMIT 10
        """
        locais_data = execute_query(local_query)
        logger.info(f"✅ Dados de locais de trabalho obtidos: {len(locais_data)} registros")
        
        result = {
            'tipos': tipos_data,
            'locais': locais_data
        }
        logger.info(f"📦 Retornando dados trabalho: {result}")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ ERRO TRABALHO: {e}")
        logger.error(f"📍 Traceback completo:", exc_info=True)
        return jsonify({'error': str(e)}), 500
