import os
import json
from datetime import datetime

def clear_previous_results():
    """Limpa resultados anteriores para nova execução"""
    
    results_dir = 'data/processed'
    
    if os.path.exists(results_dir):
        files_to_clear = [
            'comprovantes_estruturados.json',
            'dados_chatbot.json'
        ]
        
        for filename in files_to_clear:
            filepath = os.path.join(results_dir, filename)
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    print(f"✅ Removido: {filepath}")
                except Exception as e:
                    print(f"❌ Erro ao remover {filepath}: {e}")
        
        print(f"🧹 Limpeza concluída em: {results_dir}")
    else:
        print(f"📁 Diretório {results_dir} não existe")

if __name__ == "__main__":
    print("🧹 Limpando resultados anteriores...")
    clear_previous_results()
    print("✅ Pronto para nova execução!")
    print("\nExecute agora: python src/main.py")
