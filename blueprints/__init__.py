# Blueprints para modularização do sistema AMEG

from .auth import auth_bp
from .dashboard import dashboard_bp
from .cadastros import cadastros_bp
from .arquivos import arquivos_bp
from .relatorios import relatorios_bp
from .usuarios import usuarios_bp
from .caixa import caixa_bp
from .charts import charts_bp

def register_blueprints(app):
    """Registra todos os blueprints na aplicação"""
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(cadastros_bp)
    app.register_blueprint(arquivos_bp)
    app.register_blueprint(relatorios_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(caixa_bp)
    app.register_blueprint(charts_bp)
