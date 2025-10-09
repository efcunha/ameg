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
    
    # Alertas de saúde críticos
    cursor.execute("""
        SELECT nome_completo, tem_deficiencia, medicamentos_alto_custo, 
               doencas_cronicas, acesso_medicamentos
        FROM cadastros 
        WHERE tem_deficiencia = 'Sim' 
           OR medicamentos_alto_custo = 'Sim'
           OR acesso_medicamentos = 'Não'
           OR doencas_cronicas ILIKE '%diabetes%'
           OR doencas_cronicas ILIKE '%hipertensão%'
        ORDER BY data_cadastro DESC LIMIT 10
    """)
    
    for row in cursor.fetchall():
        nome, deficiencia, alto_custo, doencas, acesso = row
        
        if deficiencia == 'Sim':
            notifications.append({
                'type': 'health',
                'priority': 'high',
                'message': f'{nome} - Pessoa com deficiência cadastrada',
                'icon': '♿'
            })
        
        if alto_custo == 'Sim':
            notifications.append({
                'type': 'health', 
                'priority': 'medium',
                'message': f'{nome} - Medicamento de alto custo',
                'icon': '💊'
            })
            
        if acesso == 'Não':
            notifications.append({
                'type': 'health',
                'priority': 'urgent', 
                'message': f'{nome} - Sem acesso a medicamentos',
                'icon': '🚨'
            })
    
    cursor.close()
    conn.close()
    
    return jsonify(notifications[:5])  # Máximo 5 notificações
