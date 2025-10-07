from flask import Flask, request
from flask_compress import Compress
from database import init_db_tables, create_admin_user
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Criar aplicação Flask
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'ameg_secret_2024_fallback_key_change_in_production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Configurar compressão
Compress(app)

# Importar e registrar blueprints
from blueprints.auth import auth_bp
from blueprints.dashboard import dashboard_bp
from blueprints.cadastros import cadastros_bp
from blueprints.arquivos import arquivos_bp
from blueprints.relatorios import relatorios_bp
from blueprints.usuarios import usuarios_bp
from blueprints.caixa import caixa_bp

app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(cadastros_bp)
app.register_blueprint(arquivos_bp)
app.register_blueprint(relatorios_bp)
app.register_blueprint(usuarios_bp)
app.register_blueprint(caixa_bp)

# Headers de segurança
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# Cache para arquivos estáticos
@app.after_request
def after_request(response):
    if request.endpoint == 'static':
        response.cache_control.max_age = 31536000
        response.cache_control.public = True
    return response

logger.info("🚀 Iniciando aplicação AMEG com arquitetura de blueprints")

# Inicializar banco no Railway
if os.environ.get('RAILWAY_ENVIRONMENT'):
    logger.info("🔧 Inicializando banco PostgreSQL...")
    try:
        init_db_tables()
        create_admin_user()
        logger.info("✅ Banco inicializado no Railway")
    except Exception as e:
        logger.error(f"❌ Erro na inicialização: {e}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
