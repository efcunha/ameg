from flask import Blueprint, jsonify, session, render_template, redirect, url_for, request
from database import get_db_connection
import logging
import os

# Configurar logging apenas para desenvolvimento
if not os.environ.get('RAILWAY_ENVIRONMENT'):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
else:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.WARNING)  # Apenas warnings em produção

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/notificacoes', methods=['GET', 'POST'])
def notificacoes_simples():
    logger.info("🔔 ACESSO À ROTA /notificacoes")
    logger.info(f"Método HTTP: {request.method}")
    logger.info(f"Sessão: {session}")
    
    if 'usuario' not in session:  # CORRIGIDO: era 'user_id', agora é 'usuario'
        logger.warning("❌ Usuário não logado, redirecionando para login")
        return redirect('/login')
    
    logger.info(f"✅ Usuário logado: {session.get('usuario', 'N/A')}")
    
    try:
        logger.info("🔄 Conectando ao banco de dados...")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        logger.info("🔄 Criando tabela se não existir...")
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
        logger.info("✅ Tabela criada/verificada com sucesso")
        
        logger.info("🔄 Buscando notificações...")
        cursor.execute("""
            SELECT hn.*, c.nome_completo
            FROM historico_notificacoes hn
            LEFT JOIN cadastros c ON hn.cadastro_id = c.id
            ORDER BY hn.data_criacao DESC
            LIMIT 100
        """)
        
        notificacoes = cursor.fetchall()
        logger.info(f"✅ Encontradas {len(notificacoes)} notificações")
        
        cursor.close()
        conn.close()
        
        logger.info("🔄 Renderizando template...")
        return render_template('historico_notificacoes.html', notificacoes=notificacoes)
    
    except Exception as e:
        logger.error(f"❌ ERRO: {str(e)}")
        return f"Erro detalhado: {str(e)}"

@notifications_bp.route('/historico-notificacoes', methods=['GET'])
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

@notifications_bp.route('/api/marcar-visualizada/<int:notif_id>', methods=['GET', 'POST'])
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
