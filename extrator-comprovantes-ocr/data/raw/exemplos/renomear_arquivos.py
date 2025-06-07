import os
import glob
from pathlib import Path

def renomear_comprovantes(pasta_origem):
    """
    Renomeia todos os arquivos de imagem da pasta para comprovante_XXX.jpg
    
    Args:
        pasta_origem (str): Caminho da pasta contendo os arquivos
    """
    
    # Extensões de imagem aceitas
    extensoes_imagem = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff', '*.gif']
    
    # Lista todos os arquivos de imagem
    arquivos = []
    for extensao in extensoes_imagem:
        arquivos.extend(glob.glob(os.path.join(pasta_origem, extensao)))
        arquivos.extend(glob.glob(os.path.join(pasta_origem, extensao.upper())))
    
    # Remove arquivos que já foram renomeados (começam com "comprovante_")
    arquivos = [arq for arq in arquivos if not os.path.basename(arq).startswith('comprovante_')]
    
    # Ordena a lista para renomeação consistente
    arquivos.sort()
    
    print(f"Encontrados {len(arquivos)} arquivos de imagem para renomear")
    
    # Verificar se existem arquivos já renomeados para continuar numeração
    arquivos_existentes = glob.glob(os.path.join(pasta_origem, 'comprovante_*.jpg'))
    arquivos_existentes.extend(glob.glob(os.path.join(pasta_origem, 'comprovante_*.jpeg')))
    arquivos_existentes.extend(glob.glob(os.path.join(pasta_origem, 'comprovante_*.png')))
    
    # Determinar próximo número sequencial
    proximo_numero = len(arquivos_existentes) + 1
    
    # Renomeia cada arquivo sequencialmente
    contador = 0
    for arquivo_antigo in arquivos:
        # Obter extensão original
        extensao_original = Path(arquivo_antigo).suffix.lower()
        
        # Se não for jpg, mantém a extensão original, senão usa .jpg
        if extensao_original not in ['.jpg', '.jpeg']:
            nova_extensao = extensao_original
        else:
            nova_extensao = '.jpg'
        
        # Criar novo nome com numeração sequencial de 3 dígitos
        numero_atual = proximo_numero + contador
        novo_nome = f"comprovante_{numero_atual:03d}{nova_extensao}"
        arquivo_novo = os.path.join(pasta_origem, novo_nome)
        
        # Verificar se o arquivo já existe e ajustar número se necessário
        while os.path.exists(arquivo_novo):
            numero_atual += 1
            novo_nome = f"comprovante_{numero_atual:03d}{nova_extensao}"
            arquivo_novo = os.path.join(pasta_origem, novo_nome)
        
        try:
            # Renomear arquivo
            os.rename(arquivo_antigo, arquivo_novo)
            print(f"Renomeado: {os.path.basename(arquivo_antigo)} -> {novo_nome}")
            contador += 1
        except Exception as e:
            print(f"Erro ao renomear {arquivo_antigo}: {e}")

def main():
    # Pasta atual onde estão os arquivos
    pasta_atual = os.path.dirname(os.path.abspath(__file__))
    
    print(f"Renomeando arquivos na pasta: {pasta_atual}")
    print("-" * 50)
    
    # Confirmar antes de executar
    resposta = input("Deseja continuar com a renomeação? (s/n): ")
    if resposta.lower() in ['s', 'sim', 'y', 'yes']:
        renomear_comprovantes(pasta_atual)
        print("-" * 50)
        print("Renomeação concluída!")
    else:
        print("Operação cancelada.")

if __name__ == "__main__":
    main()
