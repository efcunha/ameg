from flask import Blueprint, jsonify, render_template
from flask_login import login_required
from database import execute_query
from datetime import datetime, timedelta

charts_bp = Blueprint('charts', __name__)

@charts_bp.route('/charts')
@login_required
def charts_page():
    """Página principal dos gráficos"""
    return render_template('charts.html')

@charts_bp.route('/api/charts/demografia')
@login_required
def demografia_data():
    """Dados demográficos para gráficos"""
    try:
        # Faixa etária
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
        
        # Bairros
        bairro_query = """
        SELECT bairro, COUNT(*) as total
        FROM cadastros 
        WHERE bairro IS NOT NULL AND bairro != ''
        GROUP BY bairro
        ORDER BY total DESC
        LIMIT 10
        """
        
        # Evolução mensal
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
        
        return jsonify({
            'idade': execute_query(idade_query),
            'bairros': execute_query(bairro_query),
            'evolucao': execute_query(evolucao_query)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@charts_bp.route('/api/charts/saude')
@login_required
def saude_data():
    """Dados de saúde para gráficos"""
    try:
        # Doenças crônicas
        doencas_query = """
        SELECT doencas_cronicas, COUNT(*) as total
        FROM cadastros 
        WHERE tem_doenca_cronica = true AND doencas_cronicas IS NOT NULL AND doencas_cronicas != ''
        GROUP BY doencas_cronicas
        ORDER BY total DESC
        LIMIT 10
        """
        
        # Medicamentos
        medicamentos_query = """
        SELECT medicamentos_uso, COUNT(*) as total
        FROM cadastros 
        WHERE medicamentos_uso IS NOT NULL AND medicamentos_uso != ''
        GROUP BY medicamentos_uso
        ORDER BY total DESC
        LIMIT 10
        """
        
        # Deficiências
        deficiencias_query = """
        SELECT deficiencia_tipo, COUNT(*) as total
        FROM cadastros 
        WHERE tem_deficiencia = true AND deficiencia_tipo IS NOT NULL AND deficiencia_tipo != ''
        GROUP BY deficiencia_tipo
        ORDER BY total DESC
        """
        
        return jsonify({
            'doencas': execute_query(doencas_query),
            'medicamentos': execute_query(medicamentos_query),
            'deficiencias': execute_query(deficiencias_query)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@charts_bp.route('/api/charts/socioeconomico')
@login_required
def socioeconomico_data():
    """Dados socioeconômicos para gráficos"""
    try:
        # Renda familiar
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
        
        # Tipos de moradia
        moradia_query = """
        SELECT casa_tipo, COUNT(*) as total
        FROM cadastros 
        WHERE casa_tipo IS NOT NULL AND casa_tipo != ''
        GROUP BY casa_tipo
        ORDER BY total DESC
        """
        
        # Benefícios sociais
        beneficios_query = """
        SELECT beneficios_sociais, COUNT(*) as total
        FROM cadastros 
        WHERE beneficios_sociais IS NOT NULL AND beneficios_sociais != ''
        GROUP BY beneficios_sociais
        ORDER BY total DESC
        """
        
        return jsonify({
            'renda': execute_query(renda_query),
            'moradia': execute_query(moradia_query),
            'beneficios': execute_query(beneficios_query)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@charts_bp.route('/api/charts/trabalho')
@login_required
def trabalho_data():
    """Dados de trabalho para gráficos"""
    try:
        # Tipos de trabalho
        trabalho_query = """
        SELECT tipo_trabalho, COUNT(*) as total
        FROM cadastros 
        WHERE tipo_trabalho IS NOT NULL AND tipo_trabalho != ''
        GROUP BY tipo_trabalho
        ORDER BY total DESC
        """
        
        # Local de trabalho
        local_query = """
        SELECT local_trabalho, COUNT(*) as total
        FROM cadastros 
        WHERE local_trabalho IS NOT NULL AND local_trabalho != ''
        GROUP BY local_trabalho
        ORDER BY total DESC
        LIMIT 10
        """
        
        return jsonify({
            'tipos': execute_query(trabalho_query),
            'locais': execute_query(local_query)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
