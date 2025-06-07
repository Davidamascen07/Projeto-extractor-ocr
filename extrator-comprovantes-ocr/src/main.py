# main.py

import os
import sys
from datetime import datetime
from pathlib import Path

# Adicionar o diretório raiz do projeto ao PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Agora as importações funcionarão corretamente
from src.ocr.extractor import OCRExtractor
from src.ml.model import MLModel
from src.utils.helpers import (
    load_image, save_results, extract_supported_image_files,
    standardize_data_for_chatbot, validate_specific_patterns
)

def create_chatbot_ready_data(comprovante_dict: dict) -> dict:
    """Cria estrutura de dados otimizada para chatbot - ETAPA 2"""
    # Padronizar dados
    standardized = standardize_data_for_chatbot(comprovante_dict)
    
    # Validar padrões específicos
    pattern_validation = validate_specific_patterns(comprovante_dict, {})
    
    # Estrutura final para chatbot
    chatbot_data = {
        'id_transacao': standardized['id_unico'],
        'resumo': {
            'tipo': standardized['tipo_transacao'],
            'valor': standardized['valor_formatado'],
            'valor_numerico': standardized['valor_numerico'],
            'data_completa': f"{standardized['data_formatada']} {standardized['hora_formatada']}".strip(),
            'status': comprovante_dict.get('situacao', 'Processado')
        },
        'participantes': {
            'origem': {
                'nome_completo': standardized['origem']['nome'],
                'documento': standardized['origem']['cpf'],
                'banco': standardized['origem']['instituicao'],
                'tipo_pessoa': 'PF' if standardized['origem']['cpf'] else 'PJ'
            },
            'destino': {
                'nome_completo': standardized['destino']['nome'],
                'documento': standardized['destino']['cpf'],
                'banco': standardized['destino']['instituicao'],
                'chave_pix': standardized['destino']['chave_pix'],
                'tipo_pessoa': 'PF' if standardized['destino']['cpf'] else 'PJ'
            }
        },
        'detalhes_operacao': {
            'codigo_transacao': standardized['detalhes_transacao']['id'],
            'codigo_autenticacao': standardized['detalhes_transacao']['autenticacao'],
            'descricao_operacao': standardized['detalhes_transacao']['descricao'],
            'tipo_operacao': 'PIX' if 'pix' in standardized['tipo_transacao'].lower() else 'Transferência',
            'canal_utilizado': standardized['metadados']['banco_detectado'].replace('_', ' ').title()
        },
        'metadados_sistema': {
            'arquivo_fonte': standardized['metadados']['arquivo_origem'],
            'data_processamento': standardized['metadados']['processado_em'],
            'nivel_confianca': standardized['metadados']['confiabilidade'],
            'validacoes': {
                'padroes_reconhecidos': pattern_validation.get('matches', []),
                'alertas': pattern_validation.get('mismatches', []),
                'score_confianca': pattern_validation.get('confidence', 0.0)
            }
        },
        'consultas_chatbot': {
            'query_valor': f"transação de {standardized['valor_formatado']}",
            'query_destinatario': f"pagamento para {standardized['destino']['nome']}",
            'query_data': f"operação em {standardized['data_formatada']}",
            'query_tipo': f"{standardized['tipo_transacao']} via {standardized['metadados']['banco_detectado']}",
            'tags_busca': [
                standardized['tipo_transacao'].lower(),
                standardized['metadados']['banco_detectado'],
                standardized['destino']['nome'].lower() if standardized['destino']['nome'] else '',
                f"valor_{int(standardized['valor_numerico'])}" if standardized['valor_numerico'] > 0 else ''
            ]
        }
    }
    
    return chatbot_data

def main():
    print("=== Sistema de Extração OCR de Comprovantes ===")
    print("Iniciando processamento...")
    
    # Configurações
    input_dir = 'data/raw/exemplos'
    output_dir = 'data/processed'
    
    # Verificar se diretório existe
    if not os.path.exists(input_dir):
        print(f"❌ Diretório não encontrado: {input_dir}")
        print("💡 Certifique-se de que o diretório existe e contém imagens")
        return
    
    # Criar diretório de saída
    os.makedirs(output_dir, exist_ok=True)
    
    # Inicializar componentes
    try:
        extractor = OCRExtractor()
        ml_model = MLModel()
        
        print("✅ Componentes inicializados")
    except Exception as e:
        print(f"❌ Erro ao inicializar componentes: {e}")
        return
    
    # Obter arquivos de imagem
    image_files = extract_supported_image_files(input_dir)
    
    if not image_files:
        print(f"❌ Nenhuma imagem encontrada em: {input_dir}")
        return
    
    print(f"📄 Encontradas {len(image_files)} imagens para processar")
    
    # Processar cada imagem
    comprovantes_estruturados = []
    resultados_detalhados = []
    
    for i, image_path in enumerate(image_files, 1):
        print(f"\n🔍 Processando {i}/{len(image_files)}: {os.path.basename(image_path)}")
        
        try:
            # Carregar e processar imagem
            image = load_image(image_path)
            
            # Extrair dados
            resultado = extractor.extract_data(image, image_path)
            
            # Adicionar metadados
            resultado['arquivo'] = os.path.basename(image_path)
            resultado['caminho_completo'] = image_path
            resultado['processado_em'] = datetime.now().isoformat()
            
            comprovantes_estruturados.append(resultado)
            
            # Log do resultado
            if resultado.get('valor_total', 0) > 0:
                print(f"  ✅ Valor extraído: R$ {resultado['valor_total']:.2f}")
            if resultado.get('pagador_nome'):
                print(f"  ✅ Pagador: {resultado['pagador_nome']}")
            if resultado.get('recebedor_nome'):
                print(f"  ✅ Recebedor: {resultado['recebedor_nome']}")
            
        except Exception as e:
            print(f"  ❌ Erro ao processar {os.path.basename(image_path)}: {e}")
            # Adicionar resultado de erro
            comprovantes_estruturados.append({
                'arquivo': os.path.basename(image_path),
                'erro': str(e),
                'processado_em': datetime.now().isoformat()
            })
    
    # Salvar resultados estruturados
    if comprovantes_estruturados:
        estruturados_path = os.path.join(output_dir, 'comprovantes_estruturados.json')
        
        estrutura_final = {
            'metadata': {
                'total_processados': len(comprovantes_estruturados),
                'com_sucesso': len([c for c in comprovantes_estruturados if 'erro' not in c]),
                'com_erro': len([c for c in comprovantes_estruturados if 'erro' in c]),
                'data_processamento': datetime.now().isoformat()
            },
            'comprovantes': comprovantes_estruturados
        }
        
        save_results(estrutura_final, estruturados_path)
        print(f"📊 Dados estruturados salvos em: {estruturados_path}")
        
        # Preparar dados para chatbot
        chatbot_ready_data = []
        
        for comprovante in comprovantes_estruturados:
            if 'erro' not in comprovante:  # Apenas comprovantes processados com sucesso
                try:
                    chatbot_data = create_chatbot_ready_data(comprovante)
                    chatbot_ready_data.append(chatbot_data)
                except Exception as e:
                    print(f"  ⚠ Erro ao preparar dados para chatbot: {e}")
        
        # Salvar dados otimizados para chatbot
        if chatbot_ready_data:
            chatbot_path = os.path.join(output_dir, 'dados_chatbot.json')
            chatbot_structure = {
                'metadata': {
                    'total_transacoes': len(chatbot_ready_data),
                    'tipos_encontrados': list(set([item['resumo']['tipo'] for item in chatbot_ready_data])),
                    'bancos_detectados': list(set([item['detalhes_operacao']['canal_utilizado'] for item in chatbot_ready_data])),
                    'valor_total_processado': sum([item['resumo']['valor_numerico'] for item in chatbot_ready_data]),
                    'periodo_cobertura': {
                        'mais_antigo': min([item['resumo']['data_completa'] for item in chatbot_ready_data if item['resumo']['data_completa']]) if any(item['resumo']['data_completa'] for item in chatbot_ready_data) else '',
                        'mais_recente': max([item['resumo']['data_completa'] for item in chatbot_ready_data if item['resumo']['data_completa']]) if any(item['resumo']['data_completa'] for item in chatbot_ready_data) else ''
                    },
                    'processado_em': datetime.now().isoformat()
                },
                'transacoes': chatbot_ready_data,
                'indices_busca': {
                    'por_destinatario': {},
                    'por_valor': {},
                    'por_tipo': {},
                    'por_banco': {}
                }
            }
            
            # Criar índices de busca para otimização do chatbot
            for transacao in chatbot_ready_data:
                # Índice por destinatário
                dest_nome = transacao['participantes']['destino']['nome_completo']
                if dest_nome:
                    if dest_nome not in chatbot_structure['indices_busca']['por_destinatario']:
                        chatbot_structure['indices_busca']['por_destinatario'][dest_nome] = []
                    chatbot_structure['indices_busca']['por_destinatario'][dest_nome].append(transacao['id_transacao'])
                
                # Índice por valor
                valor = transacao['resumo']['valor_numerico']
                if valor > 0:
                    valor_faixa = f"{int(valor//10)*10}-{int(valor//10)*10+9}"
                    if valor_faixa not in chatbot_structure['indices_busca']['por_valor']:
                        chatbot_structure['indices_busca']['por_valor'][valor_faixa] = []
                    chatbot_structure['indices_busca']['por_valor'][valor_faixa].append(transacao['id_transacao'])
                
                # Índice por tipo
                tipo = transacao['resumo']['tipo']
                if tipo not in chatbot_structure['indices_busca']['por_tipo']:
                    chatbot_structure['indices_busca']['por_tipo'][tipo] = []
                chatbot_structure['indices_busca']['por_tipo'][tipo].append(transacao['id_transacao'])
                
                # Índice por banco
                banco = transacao['detalhes_operacao']['canal_utilizado']
                if banco not in chatbot_structure['indices_busca']['por_banco']:
                    chatbot_structure['indices_busca']['por_banco'][banco] = []
                chatbot_structure['indices_busca']['por_banco'][banco].append(transacao['id_transacao'])
            
            save_results(chatbot_structure, chatbot_path)
            print(f"📱 Dados otimizados para chatbot salvos em: {chatbot_path}")
    
    # Resumo final
    print(f"\n🎉 Processamento concluído!")
    print(f"📊 Estatísticas finais:")
    print(f"   - Total de arquivos: {len(image_files)}")
    print(f"   - Processados com sucesso: {len([c for c in comprovantes_estruturados if 'erro' not in c])}")
    print(f"   - Com erro: {len([c for c in comprovantes_estruturados if 'erro' in c])}")
    if chatbot_ready_data:
        print(f"   - Dados preparados para chatbot: {len(chatbot_ready_data)}")
        print(f"   - Valor total processado: R$ {sum([item['resumo']['valor_numerico'] for item in chatbot_ready_data]):.2f}")
    
    print(f"\n📁 Arquivos gerados:")
    print(f"   - {estruturados_path}")
    if chatbot_ready_data:
        print(f"   - {chatbot_path}")
    
    print(f"\n✅ Dados prontos para treinamento do modelo e integração com chatbot!")

if __name__ == "__main__":
    main()