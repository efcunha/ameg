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

@charts_bp.route('/api/charts/filters')
@login_required
def get_filter_options():
    """Obter opções disponíveis para filtros"""
    logger.info("🔍 OBTENDO OPÇÕES DE FILTROS")
    try:
        # Obter lista de bairros
        bairros_query = """
        SELECT DISTINCT bairro
        FROM cadastros 
        WHERE bairro IS NOT NULL AND bairro != ''
        ORDER BY bairro
        """
        bairros_data = execute_query(bairros_query)
        bairros = [{'value': b['bairro'], 'label': b['bairro']} for b in bairros_data]
        
        result = {
            'bairros': bairros
        }
        logger.info(f"📦 Retornando opções de filtros: {len(bairros)} bairros")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ ERRO FILTROS: {e}")
        return jsonify({'error': str(e)}), 500

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
    
    # Obter filtros da query string
    from flask import request
    periodo = request.args.get('periodo', 'todos')
    bairro = request.args.get('bairro', 'todos')
    
    logger.info(f"🔍 Filtros aplicados - Período: {periodo}, Bairro: {bairro}")
    
    try:
        # Construir filtros WHERE
        where_conditions = []
        
        # Filtro de período
        if periodo == '6m':
            where_conditions.append("data_cadastro >= CURRENT_DATE - INTERVAL '6 months'")
        elif periodo == '1a':
            where_conditions.append("data_cadastro >= CURRENT_DATE - INTERVAL '1 year'")
        
        # Filtro de bairro
        if bairro != 'todos':
            where_conditions.append(f"bairro = '{bairro}'")
        
        where_clause = " AND " + " AND ".join(where_conditions) if where_conditions else ""
        
        # Faixa etária
        logger.info("🎂 Executando query de faixa etária...")
        idade_query = f"""
        SELECT 
            CASE 
                WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, data_nascimento)) < 18 THEN 'Menor 18'
                WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, data_nascimento)) < 30 THEN '18-29'
                WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, data_nascimento)) < 50 THEN '30-49'
                ELSE '50+'
            END as faixa,
            COUNT(*) as total
        FROM cadastros 
        WHERE data_nascimento IS NOT NULL{where_clause}
        GROUP BY faixa
        ORDER BY faixa
        """
        idade_data = execute_query(idade_query)
        
        # Se não há dados de idade válidos, criar dados alternativos
        if not idade_data:
            logger.info("🔄 Sem dados de idade válidos, usando contagem total")
            idade_fallback_query = f"""
            SELECT 'Dados disponíveis' as faixa, COUNT(*) as total
            FROM cadastros
            WHERE 1=1{where_clause}
            """
            idade_data = execute_query(idade_fallback_query)
        
        logger.info(f"✅ Dados de idade obtidos: {len(idade_data)} registros")
        
        # Bairros
        logger.info("🏘️ Executando query de bairros...")
        bairro_query = f"""
        SELECT bairro, COUNT(*) as total
        FROM cadastros 
        WHERE bairro IS NOT NULL AND bairro != ''{where_clause}
        GROUP BY bairro
        ORDER BY total DESC
        LIMIT 10
        """
        bairros_data = execute_query(bairro_query)
        logger.info(f"✅ Dados de bairros obtidos: {len(bairros_data)} registros")
        
        # Evolução mensal
        logger.info("📈 Executando query de evolução mensal...")
        evolucao_query = f"""
        SELECT 
            TO_CHAR(data_cadastro, 'YYYY-MM') as mes,
            COUNT(*) as total
        FROM cadastros 
        WHERE data_cadastro IS NOT NULL{where_clause}
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
    
    # Obter filtros da query string
    from flask import request
    periodo = request.args.get('periodo', 'todos')
    bairro = request.args.get('bairro', 'todos')
    
    logger.info(f"🔍 Filtros aplicados - Período: {periodo}, Bairro: {bairro}")
    
    try:
        # Construir filtros WHERE
        where_conditions = []
        
        # Filtro de período
        if periodo == '6m':
            where_conditions.append("data_cadastro >= CURRENT_DATE - INTERVAL '6 months'")
        elif periodo == '1a':
            where_conditions.append("data_cadastro >= CURRENT_DATE - INTERVAL '1 year'")
        
        # Filtro de bairro
        if bairro != 'todos':
            where_conditions.append(f"bairro = '{bairro}'")
        
        where_clause = " AND " + " AND ".join(where_conditions) if where_conditions else ""
        # Doenças crônicas - CORRIGIDO: tem_doenca_cronica é VARCHAR, não BOOLEAN
        logger.info("💊 Executando query de doenças crônicas...")
        doencas_query = f"""
        SELECT doencas_cronicas, COUNT(*) as total
        FROM cadastros 
        WHERE tem_doenca_cronica = 'Sim' AND doencas_cronicas IS NOT NULL AND doencas_cronicas != ''{where_clause}
        GROUP BY doencas_cronicas
        ORDER BY total DESC
        LIMIT 10
        """
        doencas_data = execute_query(doencas_query)
        logger.info(f"✅ Dados de doenças obtidos: {len(doencas_data)} registros")
        
        # Medicamentos - CORRIGIDO: campo é medicamentos_continuos, não medicamentos_uso
        logger.info("💉 Executando query de medicamentos...")
        medicamentos_query = f"""
        SELECT medicamentos_continuos, COUNT(*) as total
        FROM cadastros 
        WHERE usa_medicamento_continuo = 'Sim' AND medicamentos_continuos IS NOT NULL AND medicamentos_continuos != ''{where_clause}
        GROUP BY medicamentos_continuos
        ORDER BY total DESC
        LIMIT 10
        """
        medicamentos_data = execute_query(medicamentos_query)
        logger.info(f"✅ Dados de medicamentos obtidos: {len(medicamentos_data)} registros")
        
        # Deficiências - CORRIGIDO: campo é tipo_deficiencia, não deficiencia_tipo
        logger.info("♿ Executando query de deficiências...")
        deficiencias_query = f"""
        SELECT tipo_deficiencia, COUNT(*) as total
        FROM cadastros 
        WHERE tem_deficiencia = 'Sim' AND tipo_deficiencia IS NOT NULL AND tipo_deficiencia != ''{where_clause}
        GROUP BY tipo_deficiencia
        ORDER BY total DESC
        """
        deficiencias_data = execute_query(deficiencias_query)
        logger.info(f"✅ Dados de deficiências obtidos: {len(deficiencias_data)} registros")
        
        # Se não há dados, criar alternativos
        if not doencas_data:
            doencas_data = [{'doencas_cronicas': 'Nenhuma informação', 'total': 0}]
        if not medicamentos_data:
            medicamentos_data = [{'medicamentos_continuos': 'Nenhuma informação', 'total': 0}]
        if not deficiencias_data:
            deficiencias_data = [{'tipo_deficiencia': 'Nenhuma informação', 'total': 0}]
        
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
    
    # Obter filtros da query string
    from flask import request
    periodo = request.args.get('periodo', 'todos')
    bairro = request.args.get('bairro', 'todos')
    
    logger.info(f"🔍 Filtros aplicados - Período: {periodo}, Bairro: {bairro}")
    
    try:
        # Construir filtros WHERE
        where_conditions = []
        
        # Filtro de período
        if periodo == '6m':
            where_conditions.append("data_cadastro >= CURRENT_DATE - INTERVAL '6 months'")
        elif periodo == '1a':
            where_conditions.append("data_cadastro >= CURRENT_DATE - INTERVAL '1 year'")
        
        # Filtro de bairro
        if bairro != 'todos':
            where_conditions.append(f"bairro = '{bairro}'")
        
        where_clause = " AND " + " AND ".join(where_conditions) if where_conditions else ""
        # Renda familiar - CORRIGIDO: usar ::text para regex
        logger.info("💵 Executando query de renda familiar...")
        renda_query = f"""
        SELECT 
            CASE 
                WHEN renda_familiar::text ~ '^[0-9]+\.?[0-9]*$' AND renda_familiar::numeric < 1000 THEN 'Até R$ 1.000'
                WHEN renda_familiar::text ~ '^[0-9]+\.?[0-9]*$' AND renda_familiar::numeric < 2000 THEN 'R$ 1.000 - R$ 2.000'
                WHEN renda_familiar::text ~ '^[0-9]+\.?[0-9]*$' AND renda_familiar::numeric < 3000 THEN 'R$ 2.000 - R$ 3.000'
                WHEN renda_familiar::text ~ '^[0-9]+\.?[0-9]*$' THEN 'Acima R$ 3.000'
                ELSE 'Não informado'
            END as faixa_renda,
            COUNT(*) as total
        FROM cadastros 
        WHERE renda_familiar IS NOT NULL{where_clause}
        GROUP BY faixa_renda
        ORDER BY total DESC
        """
        renda_data = execute_query(renda_query)
        
        # Se não há dados de renda válidos, criar dados alternativos
        if not renda_data:
            logger.info("🔄 Sem dados de renda válidos, usando contagem total")
            renda_fallback_query = f"""
            SELECT 'Dados disponíveis' as faixa_renda, COUNT(*) as total
            FROM cadastros
            WHERE 1=1{where_clause}
            """
            renda_data = execute_query(renda_fallback_query)
        
        logger.info(f"✅ Dados de renda obtidos: {len(renda_data)} registros")
        
        # Tipos de moradia
        logger.info("🏠 Executando query de tipos de moradia...")
        moradia_query = f"""
        SELECT casa_tipo, COUNT(*) as total
        FROM cadastros 
        WHERE casa_tipo IS NOT NULL AND casa_tipo != ''{where_clause}
        GROUP BY casa_tipo
        ORDER BY total DESC
        """
        moradia_data = execute_query(moradia_query)
        logger.info(f"✅ Dados de moradia obtidos: {len(moradia_data)} registros")
        
        # Benefícios sociais
        logger.info("🎁 Executando query de benefícios sociais...")
        beneficios_query = f"""
        SELECT beneficios_sociais, COUNT(*) as total
        FROM cadastros 
        WHERE beneficios_sociais IS NOT NULL AND beneficios_sociais != ''{where_clause}
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
    
    # Obter filtros da query string
    from flask import request
    periodo = request.args.get('periodo', 'todos')
    bairro = request.args.get('bairro', 'todos')
    
    logger.info(f"🔍 Filtros aplicados - Período: {periodo}, Bairro: {bairro}")
    
    try:
        # Construir filtros WHERE
        where_conditions = []
        
        # Filtro de período
        if periodo == '6m':
            where_conditions.append("data_cadastro >= CURRENT_DATE - INTERVAL '6 months'")
        elif periodo == '1a':
            where_conditions.append("data_cadastro >= CURRENT_DATE - INTERVAL '1 year'")
        
        # Filtro de bairro
        if bairro != 'todos':
            where_conditions.append(f"bairro = '{bairro}'")
        
        where_clause = " AND " + " AND ".join(where_conditions) if where_conditions else ""
        
        # Tipos de trabalho
        logger.info("🔨 Executando query de tipos de trabalho...")
        trabalho_query = f"""
        SELECT tipo_trabalho, COUNT(*) as total
        FROM cadastros 
        WHERE tipo_trabalho IS NOT NULL AND tipo_trabalho != ''{where_clause}
        GROUP BY tipo_trabalho
        ORDER BY total DESC
        """
        tipos_data = execute_query(trabalho_query)
        logger.info(f"✅ Dados de tipos de trabalho obtidos: {len(tipos_data)} registros")
        
        # Local de trabalho
        logger.info("📍 Executando query de locais de trabalho...")
        local_query = f"""
        SELECT local_trabalho, COUNT(*) as total
        FROM cadastros 
        WHERE local_trabalho IS NOT NULL AND local_trabalho != ''{where_clause}
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
