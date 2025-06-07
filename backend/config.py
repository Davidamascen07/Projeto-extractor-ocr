import os
from pathlib import Path

class Config:
    # Paths
    PROJECT_ROOT = Path(__file__).parent.parent
    UPLOAD_FOLDER = 'temp_uploads'
    DATA_FOLDER = PROJECT_ROOT / 'data' / 'processed'
    
    # API Settings
    API_HOST = '0.0.0.0'
    API_PORT = 5000
    DEBUG = True
    
    # File Upload
    MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
    
    # CORS
    CORS_ORIGINS = ['http://localhost:3000', 'http://127.0.0.1:3000']
    
    # OCR Settings
    TESSERACT_CMD = 'tesseract'  # Ajustar conforme instalação
    
    @staticmethod
    def init_app(app):
        """Inicializar configurações da aplicação"""
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.DATA_FOLDER, exist_ok=True)
