#!/usr/bin/env python3
"""
Script para instalar dependências do projeto
"""

import subprocess
import sys
from pathlib import Path

def install_requirements():
    """Instalar dependências via pip"""
    requirements_file = Path(__file__).parent / 'requirements.txt'
    
    if not requirements_file.exists():
        print("❌ Arquivo requirements.txt não encontrado!")
        return False
    
    try:
        print("📦 Instalando dependências...")
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)
        ])
        print("✅ Dependências instaladas com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar dependências: {e}")
        return False

def main():
    print("🔧 PIXText.ai - Instalador de Dependências")
    print("=" * 50)
    
    if install_requirements():
        print("\n🎉 Pronto! Execute agora:")
        print("   python run_full_system.py")
    else:
        print("\n❌ Instalação falhou. Tente manualmente:")
        print("   pip install flask flask-cors pillow")

if __name__ == "__main__":
    main()
