import os


class Config:
    SECRET_KEY = os.getenv(
        'SECRET_KEY',
        'dev-secret-key-change-me-1234567890',
    )
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///local.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True}
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')
    ES_URL = os.getenv('ES_URL', 'http://localhost:9200')
    AUTO_SEED_DEMO_DATA = os.getenv('AUTO_SEED_DEMO_DATA', 'true').lower() == 'true'
