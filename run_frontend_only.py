#!/usr/bin/env python3
"""
Script para executar apenas o frontend
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    print("🌐 PIXText.ai - Frontend")
    print("=" * 40)
    
    frontend_dir = Path(__file__).parent / 'frontend'
    
    if not frontend_dir.exists():
        print("❌ Diretório frontend não encontrado!")
        return
    
    print("🚀 Iniciando servidor frontend...")
    print("📍 Acesse: http://localhost:3000")
    print("💡 Pressione Ctrl+C para parar")
    
    try:
        os.chdir(frontend_dir)
        subprocess.run([sys.executable, '-m', 'http.server', '3000'])
    except KeyboardInterrupt:
        print("\n👋 Frontend finalizado!")
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    main()
