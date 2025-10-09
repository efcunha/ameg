from flask import Blueprint, jsonify, session, render_template, redirect, url_for
from database import get_db_connection

notifications_bp = Blueprint('notifications', __name__)

def salvar_notificacao_historico(tipo, prioridade, mensagem, icone, cadastro_id=None):
    """Salva notificação no histórico"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar se já existe para evitar duplicatas
    cursor.execute("""
        SELECT id FROM historico_notificacoes 
        WHERE mensagem = %s AND DATE(data_criacao) = CURRENT_DATE
    """, (mensagem,))
    
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO historico_notificacoes 
            (tipo, prioridade, mensagem, icone, cadastro_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (tipo, prioridade, mensagem, icone, cadastro_id))
        conn.commit()
    
    cursor.close()
    conn.close()

@notifications_bp.route('/api/notifications')
def get_notifications():
    if 'user_id' not in session:
        return jsonify([])
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    notifications = []
    
    # Buscar dados de saúde da tabela dados_saude_pessoa
    cursor.execute("""
        SELECT c.id, c.nome_completo, dsp.tem_deficiencia, dsp.deficiencias,
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
        cadastro_id, nome, deficiencia, tipo_def, doencas, medicamentos = row
        
        if deficiencia == 'Sim':
            mensagem = f'{nome} - Pessoa com deficiência: {tipo_def or "Não especificada"}'
            notifications.append({
                'type': 'health',
                'priority': 'high',
                'message': mensagem,
                'icon': '♿'
            })
            salvar_notificacao_historico('health', 'high', mensagem, '♿', cadastro_id)
            
        if doencas and any(d in doencas.lower() for d in ['diabetes', 'hipertensão', 'cardíaca']):
            mensagem = f'{nome} - Doença crônica grave: {doencas[:30]}...'
            notifications.append({
                'type': 'health',
                'priority': 'urgent', 
                'message': mensagem,
                'icon': '🚨'
            })
            salvar_notificacao_historico('health', 'urgent', mensagem, '🚨', cadastro_id)
    
    cursor.close()
    conn.close()
    
    return jsonify(notifications[:5])  # Máximo 5 notificações

@notifications_bp.route('/historico-notificacoes')
def historico_notificacoes():
    if 'user_id' not in session:
        return redirect('/login')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar se a tabela existe, se não, criar
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historico_notificacoes (
                id SERIAL PRIMARY KEY,
                tipo VARCHAR(20) NOT NULL,
                prioridade VARCHAR(10) NOT NULL,
                mensagem TEXT NOT NULL,
                icone VARCHAR(10),
                cadastro_id INTEGER REFERENCES cadastros(id) ON DELETE CASCADE,
                visualizada BOOLEAN DEFAULT FALSE,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_visualizacao TIMESTAMP
            )
        """)
        conn.commit()
        
        cursor.execute("""
            SELECT hn.*, c.nome_completo
            FROM historico_notificacoes hn
            LEFT JOIN cadastros c ON hn.cadastro_id = c.id
            ORDER BY hn.data_criacao DESC
            LIMIT 100
        """)
        
        notificacoes = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return render_template('historico_notificacoes.html', notificacoes=notificacoes)
    
    except Exception as e:
        return f"Erro: {str(e)}"

@notifications_bp.route('/api/marcar-visualizada/<int:notif_id>')
def marcar_visualizada(notif_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Não autorizado'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE historico_notificacoes 
        SET visualizada = TRUE, data_visualizacao = CURRENT_TIMESTAMP
        WHERE id = %s
    """, (notif_id,))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'success': True})
