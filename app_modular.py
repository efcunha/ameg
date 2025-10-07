from flask import Flask
from flask_compress import Compress
from database import init_db_tables, create_admin_user
import os
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Factory function para criar a aplicação Flask"""
    app = Flask(__name__)
    
    # Configurações
    app.secret_key = os.environ.get('SECRET_KEY', 'chave-super-secreta-ameg-2024')
    
    # Compressão
    Compress(app)
    
    # Registrar blueprints
    from blueprints.auth import auth_bp
    from blueprints.dashboard import dashboard_bp
    from blueprints.cadastros import cadastros_bp
    from blueprints.relatorios import relatorios_bp
    from blueprints.caixa import caixa_bp
    from blueprints.usuarios import usuarios_bp
    from blueprints.arquivos import arquivos_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(cadastros_bp)
    app.register_blueprint(relatorios_bp)
    app.register_blueprint(caixa_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(arquivos_bp)
    
    # Rotas estáticas
    @app.route('/logo')
    def logo():
        return app.send_static_file('img/logo-ameg.jpeg')
    
    # Headers de segurança
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response
    
    return app

# Criar aplicação
app = create_app()

if __name__ == '__main__':
    logger.info("🚀 Iniciando aplicação AMEG modular")
    
    # Inicializar banco de dados
    try:
        logger.info("🔧 Inicializando banco de dados...")
        init_db_tables()
        create_admin_user()
        logger.info("✅ Banco inicializado com sucesso")
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar banco: {e}")
    
    # Executar aplicação
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
