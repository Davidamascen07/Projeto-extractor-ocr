#!/usr/bin/env python3
"""
Script para executar o sistema completo: Backend API + Frontend
"""

import subprocess
import sys
import os
import threading
import time
from pathlib import Path

def run_backend():
    """Executar API backend"""
    print("🚀 Iniciando Backend API...")
    try:
        subprocess.run([sys.executable, 'backend/api.py'], cwd=Path(__file__).parent)
    except KeyboardInterrupt:
        print("\n💡 Backend finalizado")

def run_frontend():
    """Executar servidor frontend"""
    print("🌐 Iniciando Frontend...")
    try:
        # Usar servidor HTTP simples do Python
        os.chdir(Path(__file__).parent / 'frontend')
        subprocess.run([sys.executable, '-m', 'http.server', '3000'])
    except KeyboardInterrupt:
        print("\n💡 Frontend finalizado")

def check_ocr_modules():
    """Verificar se módulos OCR estão disponíveis"""
    project_root = Path(__file__).parent
    ocr_project_path = project_root / 'extrator-comprovantes-ocr'
    
    # Verificar se arquivos principais existem
    extractor_file = ocr_project_path / 'src' / 'ocr' / 'extractor.py'
    helpers_file = ocr_project_path / 'src' / 'utils' / 'helpers.py'
    
    if not extractor_file.exists():
        print(f"⚠️  Arquivo não encontrado: {extractor_file}")
        return False
    
    if not helpers_file.exists():
        print(f"⚠️  Arquivo não encontrado: {helpers_file}")
        return False
    
    return True

def main():
    print("=" * 60)
    print("🎯 PIXText.ai - Sistema Completo de Extração OCR")
    print("=" * 60)
    
    print("\n📋 Verificando dependências...")
    
    # Verificar estrutura de diretórios - ajustada para o projeto real
    project_root = Path(__file__).parent
    
    required_dirs = [
        'backend', 
        'frontend', 
        'extrator-comprovantes-ocr/src', 
        'extrator-comprovantes-ocr/data'
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        print(f"❌ Diretórios não encontrados: {missing_dirs}")
        print("\n📁 Estrutura esperada:")
        print("   c:\\projeto\\TCC subir git\\")
        print("   ├── backend\\")
        print("   ├── frontend\\")
        print("   └── extrator-comprovantes-ocr\\")
        print("       ├── src\\")
        print("       └── data\\")
        return
    
    print("✅ Estrutura de diretórios OK")
    
    # Verificar módulos OCR
    if check_ocr_modules():
        print("✅ Módulos OCR encontrados")
    else:
        print("⚠️  Módulos OCR não encontrados - executando em modo simulado")
    
    # Verificar se backend/api.py existe
    api_file = project_root / 'backend' / 'api.py'
    if not api_file.exists():
        print("⚠️  Arquivo backend/api.py não encontrado!")
        print("   Criando estrutura backend...")
        
        # Criar diretório backend se não existir
        backend_dir = project_root / 'backend'
        backend_dir.mkdir(exist_ok=True)
        
        print("   📝 Execute primeiro: Crie o arquivo backend/api.py")
        print("   💡 Ou execute apenas o frontend com: cd frontend && python -m http.server 3000")
        return
    
    try:
        print("\n🚀 Iniciando serviços...")
        
        # Executar backend em thread separada
        backend_thread = threading.Thread(target=run_backend)
        backend_thread.daemon = True
        backend_thread.start()
        
        # Aguardar backend inicializar
        time.sleep(3)
        
        print("\n🌐 Acesse o sistema em:")
        print("   Frontend: http://localhost:3000")
        print("   API:      http://localhost:5000")
        print("   Chatbot:  http://localhost:3000/chatbot.html")
        
        print("\n💡 Pressione Ctrl+C para parar o sistema")
        
        # Executar frontend (bloqueia thread principal)
        run_frontend()
        
    except KeyboardInterrupt:
        print("\n\n👋 Sistema finalizado!")
    except Exception as e:
        print(f"\n❌ Erro ao iniciar sistema: {e}")

if __name__ == "__main__":
    main()
