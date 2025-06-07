"""
Módulo de modelos de machine learning para extração de dados de comprovantes.

Este módulo contém os modelos treinados e utilitários para classificação
e estruturação de dados extraídos de comprovantes financeiros.
"""

__version__ = "1.0.0"
__author__ = "Extrator Comprovantes OCR Team"

# Configurações padrão para modelos
DEFAULT_MODEL_CONFIG = {
    "classifier_model": "comprovante_classifier.pkl",
    "feature_extractor": "tfidf_vectorizer.pkl",
    "document_types": [
        "Comprovante PIX",
        "Comprovante Transferência", 
        "Comprovante Pagamento",
        "Comprovante Boleto",
        "Comprovante Genérico"
    ],
    "confidence_threshold": 0.7,
    "max_features": 1000
}

def get_model_path(model_name: str) -> str:
    """Retorna o caminho completo para um modelo"""
    import os
    return os.path.join(os.path.dirname(__file__), model_name)

def list_available_models() -> list:
    """Lista todos os modelos disponíveis no diretório"""
    import os
    model_dir = os.path.dirname(__file__)
    models = []
    
    for file in os.listdir(model_dir):
        if file.endswith('.pkl') or file.endswith('.joblib'):
            models.append(file)
    
    return models
