#!/usr/bin/env python3
"""
Script principal para executar a extração OCR de comprovantes.
Execute este arquivo da raiz do projeto para evitar problemas de importação.

Uso:
    python run_extraction.py
"""

import os
import sys
from pathlib import Path

# Garantir que o diretório atual está no PYTHONPATH
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Importar o main do módulo src
try:
    from src.main import main
    
    if __name__ == "__main__":
        print("🚀 Iniciando Sistema de Extração OCR de Comprovantes")
        print("=" * 60)
        
        # Verificar se diretórios necessários existem
        required_dirs = [
            'data/raw/exemplos',
            'src/ocr',
            'src/ml',
            'src/utils'
        ]
        
        missing_dirs = []
        for dir_path in required_dirs:
            if not os.path.exists(dir_path):
                missing_dirs.append(dir_path)
        
        if missing_dirs:
            print("❌ Diretórios necessários não encontrados:")
            for dir_path in missing_dirs:
                print(f"   - {dir_path}")
            print("\n💡 Certifique-se de estar executando da raiz do projeto")
            sys.exit(1)
        
        # Executar o processamento principal
        main()
        
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    print("💡 Certifique-se de que todas as dependências estão instaladas:")
    print("   pip install pytesseract opencv-python scikit-learn pandas")
    sys.exit(1)
except Exception as e:
    print(f"❌ Erro durante a execução: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
