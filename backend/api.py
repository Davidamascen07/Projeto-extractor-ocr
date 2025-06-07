from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sys
from datetime import datetime
import json
import tempfile
from pathlib import Path
from werkzeug.utils import secure_filename

# Adicionar path do sistema OCR - CORRIGIDO
project_root = Path(__file__).parent.parent
ocr_project_path = project_root / 'extrator-comprovantes-ocr'
sys.path.insert(0, str(ocr_project_path))

# Importar extrator OCR existente
try:
    from src.ocr.extractor import OCRExtractor
    from src.utils.helpers import load_image, standardize_data_for_chatbot
    OCR_AVAILABLE = True
    print("✅ Módulos OCR carregados com sucesso")
except ImportError as e:
    print(f"⚠️  Erro ao importar módulos OCR: {e}")
    print("💡 Executando em modo simulado (sem OCR real)")
    OCR_AVAILABLE = False

app = Flask(__name__)
CORS(app)

# Configurações
UPLOAD_FOLDER = 'temp_uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Inicializar extrator OCR apenas se disponível
if OCR_AVAILABLE:
    try:
        extractor = OCRExtractor()
        print("✅ OCRExtractor inicializado")
    except Exception as e:
        print(f"⚠️  Erro ao inicializar OCRExtractor: {e}")
        OCR_AVAILABLE = False

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/health', methods=['GET'])
def health_check():
    """Verificar se API está funcionando"""
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/extract', methods=['POST'])
def extract_text():
    """Extrair dados de comprovante enviado"""
    try:
        # Verificar se arquivo foi enviado
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Arquivo vazio'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Tipo de arquivo não suportado'}), 400
        
        # Salvar arquivo temporariamente
        filename = secure_filename(file.filename)
        temp_path = os.path.join(UPLOAD_FOLDER, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}")
        file.save(temp_path)
        
        # Processar com OCR ou simular
        if OCR_AVAILABLE:
            # Usar OCR real
            image = load_image(temp_path)
            result = extractor.extract_data(image, temp_path)
        else:
            # Simular extração para desenvolvimento
            result = simulate_extraction(filename)
        
        # Limpar arquivo temporário
        os.remove(temp_path)
        
        # Padronizar resposta
        response = {
            'success': True,
            'data': result,
            'processed_at': datetime.now().isoformat(),
            'filename': filename,
            'mode': 'real' if OCR_AVAILABLE else 'simulated'
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Erro na extração: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'processed_at': datetime.now().isoformat()
        }), 500

def simulate_extraction(filename):
    """Simular extração de dados para desenvolvimento"""
    return {
        'layout_detectado': 'simulado',
        'valor_total': 1247.90,
        'valor_numerico': 1247.90,
        'destino_nome': 'Maria Fernanda Oliveira Santos',
        'destino_cpf': '123.456.789-00',
        'origem_nome': 'Carlos Roberto Silva',
        'data_hora': '15/07/2023 14:23',
        'codigo_operacao': 'PIX9H832FJ73G',
        'raw_text': f'SIMULAÇÃO - Arquivo: {filename}\nValor: R$ 1.247,90\nDestino: Maria Fernanda Oliveira Santos\nCPF: 123.456.789-00\nData: 15/07/2023 14:23\nID: PIX9H832FJ73G',
        'cleaned_text': 'Dados simulados para desenvolvimento'
    }

@app.route('/api/chat', methods=['POST'])
def chat_query():
    """Processar consulta do chatbot"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        context = data.get('context', {})
        
        # Carregar dados processados para consulta
        chatbot_data_path = ocr_project_path / 'data' / 'processed' / 'dados_chatbot.json'
        
        if chatbot_data_path.exists():
            with open(chatbot_data_path, 'r', encoding='utf-8') as f:
                chatbot_data = json.load(f)
        else:
            # Dados simulados se arquivo não existir
            chatbot_data = {
                'transacoes': [{
                    'resumo': {
                        'valor_numerico': 1247.90,
                        'tipo': 'PIX',
                        'data_completa': '15/07/2023 14:23'
                    },
                    'participantes': {
                        'destino': {
                            'nome_completo': 'Maria Fernanda Oliveira Santos'
                        }
                    },
                    'detalhes_operacao': {
                        'canal_utilizado': 'Nu Pagamentos S.A.'
                    },
                    'metadados_sistema': {
                        'data_processamento': datetime.now().isoformat()
                    }
                }]
            }
        
        # Processar consulta
        response = process_chat_query(message, context, chatbot_data)
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Erro no chat: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'response': 'Desculpe, ocorreu um erro ao processar sua consulta.'
        }), 500

def process_chat_query(message, context, chatbot_data):
    """Processar consulta do chatbot com dados reais"""
    message_lower = message.lower()
    transacoes = chatbot_data.get('transacoes', [])
    
    # Filtrar transações válidas (com valor > 0)
    transacoes_validas = [t for t in transacoes if t.get('resumo', {}).get('valor_numerico', 0) > 0]
    
    # Consultas por valor
    if any(word in message_lower for word in ['valor', 'quanto', 'preço', 'total', 'dinheiro']):
        if 'total' in message_lower or 'soma' in message_lower:
            total = sum(t['resumo']['valor_numerico'] for t in transacoes_validas)
            quantidade = len(transacoes_validas)
            medio = total / quantidade if quantidade > 0 else 0
            
            return {
                'success': True,
                'response': f'''💰 **Análise de Valores:**

• **Total movimentado:** R$ {total:.2f}
• **Transações válidas:** {quantidade}
• **Valor médio:** R$ {medio:.2f}
• **Maior transação:** R$ {max([t['resumo']['valor_numerico'] for t in transacoes_validas]) if transacoes_validas else 0:.2f}
• **Menor transação:** R$ {min([t['resumo']['valor_numerico'] for t in transacoes_validas]) if transacoes_validas else 0:.2f}''',
                'data': {
                    'total_value': total,
                    'count': quantidade,
                    'average': medio
                }
            }
        else:
            # Mostrar alguns valores
            valores_exemplo = [(t['resumo']['valor_numerico'], t['metadados_sistema']['arquivo_fonte']) 
                             for t in transacoes_validas][:5]
            valores_texto = [f"R$ {v[0]:.2f} ({v[1]})" for v in valores_exemplo]
            
            return {
                'success': True,
                'response': f'''💰 **Valores encontrados (últimos 5):**

{chr(10).join(f"• {valor}" for valor in valores_texto)}

💡 Para ver o total, pergunte: "Qual o valor total?"''',
                'data': {'sample_values': valores_exemplo}
            }
    
    # Consultas por destinatário/remetente
    elif any(word in message_lower for word in ['destinatário', 'destino', 'para', 'recebedor', 'quem recebeu']):
        destinatarios = {}
        for t in transacoes_validas:
            nome = t.get('participantes', {}).get('destino', {}).get('nome_completo', '')
            if nome and nome.strip():
                destinatarios[nome] = destinatarios.get(nome, 0) + t['resumo']['valor_numerico']
        
        if destinatarios:
            dest_texto = [f"• **{nome}**: R$ {valor:.2f}" for nome, valor in list(destinatarios.items())[:5]]
            return {
                'success': True,
                'response': f'''👥 **Destinatários identificados:**

{chr(10).join(dest_texto)}

💡 Foram encontrados {len(destinatarios)} destinatário(s) únicos''',
                'data': {'recipients': destinatarios}
            }
        else:
            return {
                'success': True,
                'response': '👥 Nenhum destinatário foi identificado nos comprovantes processados.',
                'data': {'recipients': {}}
            }
    
    # Consultas por banco/instituição
    elif any(word in message_lower for word in ['banco', 'instituição', 'canal', 'onde']):
        bancos = {}
        for t in transacoes:
            canal = t.get('detalhes_operacao', {}).get('canal_utilizado', 'Não identificado')
            if canal and canal != 'Generico':
                bancos[canal] = bancos.get(canal, 0) + 1
        
        if bancos:
            banco_texto = [f"• **{banco}**: {count} transação(ões)" for banco, count in bancos.items()]
            return {
                'success': True,
                'response': f'''🏦 **Instituições utilizadas:**

{chr(10).join(banco_texto)}

📊 Total: {len(bancos)} instituição(ões) diferentes''',
                'data': {'banks': bancos}
            }
        else:
            return {
                'success': True,
                'response': '🏦 Nenhuma instituição específica foi identificada claramente.',
                'data': {'banks': {}}
            }
    
    # Consultas por data/período
    elif any(word in message_lower for word in ['data', 'quando', 'período', 'dia', 'mês']):
        transacoes_com_data = [t for t in transacoes_validas 
                              if t.get('resumo', {}).get('data_completa')]
        
        if transacoes_com_data:
            datas = [t['resumo']['data_completa'] for t in transacoes_com_data]
            return {
                'success': True,
                'response': f'''📅 **Datas das transações:**

{chr(10).join(f"• {data}" for data in datas[:5])}

📊 {len(transacoes_com_data)} transação(ões) com data identificada''',
                'data': {'dates': datas}
            }
        else:
            return {
                'success': True,
                'response': '📅 Poucas datas foram identificadas nos comprovantes processados.',
                'data': {'dates': []}
            }
    
    # Relatório completo
    elif any(word in message_lower for word in ['relatório', 'resumo', 'report', 'geral', 'completo']):
        total_transacoes = len(transacoes)
        transacoes_validas_count = len(transacoes_validas)
        total_valor = sum(t['resumo']['valor_numerico'] for t in transacoes_validas)
        
        # Tipos de transação
        tipos = {}
        for t in transacoes:
            tipo = t.get('resumo', {}).get('tipo', 'Não identificado')
            tipos[tipo] = tipos.get(tipo, 0) + 1
        
        # Canais
        canais = {}
        for t in transacoes:
            canal = t.get('detalhes_operacao', {}).get('canal_utilizado', 'Não identificado')
            canais[canal] = canais.get(canal, 0) + 1
        
        return {
            'success': True,
            'response': f'''📊 **RELATÓRIO COMPLETO**

**📈 Resumo Geral:**
• Total de comprovantes: {total_transacoes}
• Transações com valor: {transacoes_validas_count}
• Valor total: R$ {total_valor:.2f}
• Valor médio: R$ {(total_valor/transacoes_validas_count) if transacoes_validas_count > 0 else 0:.2f}

**📋 Tipos de transação:**
{chr(10).join(f"• {tipo}: {count}" for tipo, count in tipos.items())}

**🏦 Canais utilizados:**
{chr(10).join(f"• {canal}: {count}" for canal, count in canais.items())}

**🔍 Qualidade dos dados:**
• Nível alto: {len([t for t in transacoes if t.get('metadados_sistema', {}).get('nivel_confianca') == 'alta'])}
• Nível médio: {len([t for t in transacoes if t.get('metadados_sistema', {}).get('nivel_confianca') == 'media'])}
• Nível baixo: {len([t for t in transacoes if t.get('metadados_sistema', {}).get('nivel_confianca') == 'baixa'])}''',
            'data': {
                'total_transactions': total_transacoes,
                'valid_transactions': transacoes_validas_count,
                'total_value': total_valor,
                'types': tipos,
                'channels': canais
            }
        }
    
    # Resposta padrão com sugestões baseadas nos dados
    else:
        sugestoes = []
        if transacoes_validas:
            sugestoes = [
                f"💰 'Qual o valor total?' (R$ {sum(t['resumo']['valor_numerico'] for t in transacoes_validas):.2f} disponível)",
                "👥 'Quem são os destinatários?'",
                "🏦 'Quais bancos foram utilizados?'",
                "📊 'Gere um relatório completo'"
            ]
        else:
            sugestoes = [
                "📄 Envie um comprovante PIX para começar",
                "❓ 'Como funciona a extração?'",
                "💡 'Que tipos de arquivo posso enviar?'"
            ]
        
        return {
            'success': True,
            'response': f'''🤖 Posso ajudar com informações sobre seus comprovantes PIX!

**💡 Perguntas que posso responder:**
{chr(10).join(sugestoes)}

**📊 Dados disponíveis:** {len(transacoes)} comprovante(s) processado(s)''',
            'data': {'suggestions': sugestoes, 'available_data': len(transacoes)}
        }

@app.route('/api/data/summary', methods=['GET'])
def get_data_summary():
    """Obter resumo dos dados processados"""
    try:
        chatbot_data_path = ocr_project_path / 'data' / 'processed' / 'dados_chatbot.json'
        
        if not chatbot_data_path.exists():
            # Retornar dados simulados
            return jsonify({
                'total_transactions': 1,
                'total_value': 1247.90,
                'transaction_types': ['PIX'],
                'banks': ['Nu Pagamentos S.A.'],
                'last_updated': datetime.now().isoformat(),
                'mode': 'simulated'
            })
        
        with open(chatbot_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        transacoes = data.get('transacoes', [])
        
        summary = {
            'total_transactions': len(transacoes),
            'total_value': sum(t['resumo']['valor_numerico'] for t in transacoes if t['resumo']['valor_numerico'] > 0),
            'transaction_types': list(set(t['resumo']['tipo'] for t in transacoes)),
            'banks': list(set(t['detalhes_operacao']['canal_utilizado'] for t in transacoes)),
            'last_updated': max([t['metadados_sistema']['data_processamento'] for t in transacoes]) if transacoes else None,
            'mode': 'real'
        }
        
        return jsonify(summary)
        
    except Exception as e:
        print(f"Erro no summary: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print(f"🚀 PIXText.ai Backend API")
    print(f"📁 Projeto OCR: {ocr_project_path}")
    print(f"🔧 Modo OCR: {'Real' if OCR_AVAILABLE else 'Simulado'}")
    print(f"🌐 Acesse: http://localhost:5000")
    print("-" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
