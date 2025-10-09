from flask import Flask, request
from flask_compress import Compress
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from database import init_db_tables, create_admin_user, get_db_connection
import os
import gzip
import logging
from datetime import datetime

# Configurar logging seguro
logging.basicConfig(
    level=logging.INFO if os.environ.get('RAILWAY_ENVIRONMENT') else logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Filtro para remover dados sensíveis dos logs
class SensitiveDataFilter(logging.Filter):
    def filter(self, record):
        if hasattr(record, 'msg'):
            # Remover senhas, CPFs, etc dos logs
            sensitive_patterns = ['senha', 'password', 'cpf', 'rg']
            msg = str(record.msg).lower()
            for pattern in sensitive_patterns:
                if pattern in msg:
                    record.msg = record.msg.replace(record.msg, '[DADOS SENSÍVEIS REMOVIDOS]')
        return True

logger.addFilter(SensitiveDataFilter())

# Criar aplicação Flask
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'ameg_secret_2024_fallback_key_change_in_production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Configurar compressão, CSRF e rate limiting
Compress(app)
csrf = CSRFProtect(app)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Função helper para verificar se usuário é admin
def is_admin_user(username):
    """Verifica se o usuário tem privilégios de administrador"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT tipo FROM usuarios WHERE usuario = %s', (username,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            tipo = result[0] if isinstance(result, tuple) else result.get('tipo', 'usuario')
            return tipo == 'admin'
        return username == 'admin'  # Fallback para compatibilidade
    except Exception as e:
        logger.error(f"Erro ao verificar admin: {e}")
        return username == 'admin'  # Fallback em caso de erro

# Registrar função como global do Jinja2
@app.context_processor
def inject_template_vars():
    return dict(is_admin_user=is_admin_user)

# Importar e registrar blueprints
from blueprints.auth import auth_bp
from blueprints.dashboard import dashboard_bp
from blueprints.cadastros import cadastros_bp
from blueprints.arquivos import arquivos_bp
from blueprints.relatorios import relatorios_bp
from blueprints.usuarios import usuarios_bp
from blueprints.caixa import caixa_bp
from blueprints.charts import charts_bp
from blueprints.notifications import notifications_bp

app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(cadastros_bp)
app.register_blueprint(arquivos_bp)
app.register_blueprint(relatorios_bp)
app.register_blueprint(usuarios_bp)
app.register_blueprint(caixa_bp)
app.register_blueprint(charts_bp)
app.register_blueprint(notifications_bp)

# Log de todas as rotas registradas
logger.info("🔍 ROTAS REGISTRADAS:")
for rule in app.url_map.iter_rules():
    logger.info(f"  {rule.rule} -> {rule.endpoint} [{', '.join(rule.methods)}]")

# Registrar API REST apenas se habilitada
if os.getenv('API_ENABLED', 'false').lower() == 'true':
    from blueprints.api import api_bp
    app.register_blueprint(api_bp)
    csrf.exempt(api_bp)  # API usa JWT, não CSRF
    logger.info("🔌 API REST habilitada em /api/v1")

# Headers de segurança
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    # Content Security Policy
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: blob:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "media-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )
    response.headers['Content-Security-Policy'] = csp
    
    return response

@app.context_processor
def inject_cdn():
    """Injeta URLs do CDN nos templates"""
    cdn_enabled = os.getenv('CDN_ENABLED', 'false').lower() == 'true'
    github_user = os.getenv('GITHUB_USER', 'efcunha')
    
    if cdn_enabled:
        cdn_base = f"https://cdn.jsdelivr.net/gh/{github_user}/ameg@main"
        return {'cdn_url': cdn_base}
    return {'cdn_url': ''}

@app.context_processor
def inject_utils():
    """Injeta funções utilitárias nos templates"""
    from blueprints.utils import is_admin_id_1
    return {'is_admin_id_1': is_admin_id_1}

# Cache para arquivos estáticos
@app.after_request
def after_request(response):
    # Adiciona headers de cache para arquivos estáticos
    if request.endpoint == 'static':
        response.cache_control.max_age = 31536000  # 1 ano
        response.cache_control.public = True
    
    # Compressão manual para arquivos CSS/JS se disponível
    if (request.endpoint == 'static' and 
        'gzip' in request.accept_encodings and
        (request.path.endswith('.css') or request.path.endswith('.js'))):
        
        gzip_path = request.path + '.gz'
        if os.path.exists('static' + gzip_path.replace('/static', '')):
            response.headers['Content-Encoding'] = 'gzip'
    
    return response

logger.info("🚀 Iniciando aplicação AMEG com arquitetura de blueprints")
logger.info(f"RAILWAY_ENVIRONMENT: {os.environ.get('RAILWAY_ENVIRONMENT')}")
logger.info(f"DATABASE_URL presente: {'DATABASE_URL' in os.environ}")
logger.debug(f"SECRET_KEY configurada: {bool(app.secret_key)}")

# Inicializar banco na inicialização (Railway ou desenvolvimento)
if os.environ.get('RAILWAY_ENVIRONMENT'):
    logger.info("🔧 Iniciando configuração do banco PostgreSQL no Railway...")
    try:
        logger.info("🔧 Inicializando tabelas do banco primeiro...")
        logger.debug("Chamando init_db_tables()...")
        init_db_tables()
        logger.info("✅ Tabelas inicializadas")
        
        logger.info("👤 Criando usuário admin...")
        logger.debug("Chamando create_admin_user()...")
        create_admin_user()
        logger.info("✅ Usuário admin configurado")
        
        logger.info("✅ Banco inicializado completamente no Railway")
    except Exception as e:
        logger.error(f"❌ Erro na inicialização do banco: {e}")
        logger.error(f"Tipo do erro: {type(e)}")
        logger.error(f"Args do erro: {e.args}")
        import traceback
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        logger.warning("⚠️ Continuando sem inicialização do banco...")
else:
    logger.info("🏠 Ambiente local detectado - inicializando PostgreSQL local...")
    try:
        init_db_tables()
        create_admin_user()
        logger.info("✅ Banco inicializado localmente")
    except Exception as e:
        logger.error(f"❌ Erro na inicialização local: {e}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
