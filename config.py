import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    DATABASE_PATH = os.environ.get('DATABASE_PATH') or 'ameg.db'
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads/saude'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
class ProductionConfig(Config):
    SECRET_KEY = os.environ.get('SECRET_KEY')
    DEBUG = False
    
class DevelopmentConfig(Config):
    DEBUG = True
    
class TestingConfig(Config):
    TESTING = True
    DATABASE_PATH = ':memory:'
