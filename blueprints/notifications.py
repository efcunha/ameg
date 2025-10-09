from flask import Blueprint, jsonify, session
from database import get_db_connection

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/api/notifications')
def get_notifications():
    if 'user_id' not in session:
        return jsonify([])
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    notifications = []
    
    # Buscar dados de saúde da tabela dados_saude_pessoa
    cursor.execute("""
        SELECT c.nome_completo, dsp.tem_deficiencia, dsp.deficiencias,
               dsp.doencas_cronicas, dsp.medicamentos
        FROM cadastros c
        JOIN dados_saude_pessoa dsp ON c.id = dsp.cadastro_id
        WHERE dsp.tem_deficiencia = 'Sim' 
           OR dsp.doencas_cronicas ILIKE '%diabetes%'
           OR dsp.doencas_cronicas ILIKE '%hipertensão%'
           OR dsp.doencas_cronicas ILIKE '%cardíaca%'
        ORDER BY c.data_cadastro DESC LIMIT 10
    """)
    
    for row in cursor.fetchall():
        nome, deficiencia, tipo_def, doencas, medicamentos = row
        
        if deficiencia == 'Sim':
            notifications.append({
                'type': 'health',
                'priority': 'high',
                'message': f'{nome} - Pessoa com deficiência: {tipo_def or "Não especificada"}',
                'icon': '♿'
            })
            
        if doencas and any(d in doencas.lower() for d in ['diabetes', 'hipertensão', 'cardíaca']):
            notifications.append({
                'type': 'health',
                'priority': 'urgent', 
                'message': f'{nome} - Doença crônica grave: {doencas[:30]}...',
                'icon': '🚨'
            })
    
    cursor.close()
    conn.close()
    
    return jsonify(notifications[:5])  # Máximo 5 notificações
