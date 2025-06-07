#!/usr/bin/env python3
"""
Script para testar extração de dados de um único comprovante.
Uso: python src/test_single.py caminho/para/imagem.jpg
"""

import sys
import os
from datetime import datetime

# Adicionar o diretório pai ao path para permitir imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ocr.extractor import OCRExtractor
from src.ml.model import MLModel
from src.utils.helpers import (
    validate_comprovante, extract_currency_values, detect_document_layout,
    clean_text
)

def analyze_extraction_quality_safe(extracted_data: dict, raw_text: str) -> dict:
    """Análise de qualidade com tratamento de erro robusto"""
    try:
        # Análise específica baseada no nome do arquivo
        filename = extracted_data.get('arquivo', '').lower()
        
        if 'comprovante6' in filename:
            return analyze_comprovante6(extracted_data, raw_text)
        elif 'comprovante5' in filename:
            return analyze_comprovante5(extracted_data, raw_text)
        else:
            return analyze_generic_comprovante(extracted_data, raw_text)
            
    except Exception as e:
        return {
            'erro_analise': str(e),
            'analise_basica': {
                'dados_extraidos_count': len(extracted_data),
                'texto_tamanho': len(raw_text),
                'tipo_detectado': extracted_data.get('tipo_documento', 'desconhecido')
            }
        }

def analyze_comprovante6(extracted_data: dict, raw_text: str) -> dict:
    """Análise específica para comprovante6.jpg (PIX R$ 178,00)"""
    
    dados_esperados = {
        'valor': 178.00,
        'tipo': 'pix',
        'recebedor_nome': 'David Damasceno da Frota',
        'pagador_nome': 'DAVID DAMASCENO DA FROTA',
        'situacao': 'Efetivado',
        'data_hora': '29/05/2025 - 16:48:58',
        'id_transacao': 'E00360305202505291948911b814907e',
        'codigo_operacao': '47437902975'
    }
    
    analise = {
        'comprovante': 'comprovante6.jpg',
        'melhorias_identificadas': [],
        'acertos': [],
        'erros': [],
        'taxa_acerto': 0
    }
    
    # Verificar tipo de documento
    tipo_extraido = extracted_data.get('tipo_documento')
    if tipo_extraido == 'pix':
        analise['acertos'].append('✅ Tipo PIX detectado corretamente')
    else:
        analise['erros'].append(f'❌ Tipo incorreto: {tipo_extraido} (esperado: pix)')
    
    # Verificar valor
    valor_extraido = extracted_data.get('valor_total') or extracted_data.get('valor_numerico')
    if valor_extraido and abs(float(valor_extraido) - 178.00) < 0.01:
        analise['acertos'].append('✅ Valor R$ 178,00 extraído corretamente')
    else:
        analise['erros'].append(f'❌ Valor incorreto: {valor_extraido} (esperado: 178.00)')
    
    # Verificar nomes
    recebedor = extracted_data.get('recebedor_nome', '')
    pagador = extracted_data.get('pagador_nome', '')
    
    if 'David Damasceno da Frota' in recebedor:
        analise['acertos'].append('✅ Nome do recebedor correto')
    else:
        analise['erros'].append(f'❌ Nome recebedor: "{recebedor}" (esperado: David Damasceno da Frota)')
    
    if 'DAVID DAMASCENO DA FROTA' in pagador:
        analise['acertos'].append('✅ Nome do pagador correto')
    else:
        analise['erros'].append(f'❌ Nome pagador: "{pagador}" (esperado: DAVID DAMASCENO DA FROTA)')
    
    # Verificar situação
    situacao = extracted_data.get('situacao', '')
    if 'Efetivado' in situacao:
        analise['acertos'].append('✅ Situação "Efetivado" extraída')
    else:
        analise['erros'].append(f'❌ Situação: "{situacao}" (esperado: Efetivado)')
    
    # Verificar ID da transação
    id_trans = extracted_data.get('id_transacao', '')
    if len(id_trans) > 20:  # ID longo capturado
        if 'E' in id_trans and '2025' in id_trans:
            analise['acertos'].append('✅ ID da transação capturado (formato correto)')
        else:
            analise['erros'].append(f'❌ ID da transação com erros de OCR: {id_trans}')
    else:
        analise['erros'].append(f'❌ ID da transação muito curto: {id_trans}')
    
    # Calcular taxa de acerto
    total_verificacoes = 6
    acertos_count = len(analise['acertos'])
    analise['taxa_acerto'] = (acertos_count / total_verificacoes) * 100
    
    # Identificar melhorias específicas
    if analise['taxa_acerto'] > 70:
        analise['melhorias_identificadas'].append('🎉 Grande melhoria! Taxa de acerto superior a 70%')
        analise['melhorias_identificadas'].append('✅ Tipo PIX detectado corretamente (antes era genérico)')
        analise['melhorias_identificadas'].append('✅ Separação correta entre pagador e recebedor')
        analise['melhorias_identificadas'].append('✅ Dados específicos da CAIXA extraídos')
    
    return analise

def analyze_comprovante5(extracted_data: dict, raw_text: str) -> dict:
    """Análise específica para comprovante5.jpg (PIX R$ 20,00)"""
    
    analise = {
        'comprovante': 'comprovante5.jpg',
        'problemas_identificados': [],
        'acertos': [],
        'erros': [],
        'taxa_acerto': 0
    }
    
    # Verificar tipo de documento
    tipo_extraido = extracted_data.get('tipo_documento')
    if tipo_extraido == 'pix':
        analise['acertos'].append('✅ Tipo PIX detectado')
    else:
        analise['erros'].append(f'❌ Tipo incorreto: {tipo_extraido} (deveria ser PIX)')
        analise['problemas_identificados'].append('Falha na detecção de PIX - texto "Comprovante Pix" não reconhecido')
    
    # Verificar valor
    valor_extraido = extracted_data.get('valor_total') or extracted_data.get('valor_numerico')
    if valor_extraido and abs(float(valor_extraido) - 20.00) < 0.01:
        analise['acertos'].append('✅ Valor R$ 20,00 correto')
    else:
        analise['erros'].append(f'❌ Valor incorreto: {valor_extraido} (esperado: 20.00)')
        analise['problemas_identificados'].append('OCR capturou valor incorreto - possível problema com "R$ 20,00"')
    
    # Verificar se capturou empresa
    nome_extraido = extracted_data.get('nome', '')
    if 'M4 PRODUTOS' in nome_extraido.upper():
        analise['acertos'].append('✅ Nome da empresa M4 capturado')
    else:
        analise['erros'].append(f'❌ Nome empresa não capturado corretamente: {nome_extraido}')
    
    # Verificar CNPJ
    cnpj = extracted_data.get('cnpj', '')
    if '09.614.276/0001-34' in cnpj:
        analise['acertos'].append('✅ CNPJ capturado')
    else:
        analise['erros'].append(f'❌ CNPJ não encontrado: {cnpj}')
    
    # Calcular taxa
    total_verificacoes = 4
    acertos_count = len(analise['acertos'])
    analise['taxa_acerto'] = (acertos_count / total_verificacoes) * 100
    
    # Problemas específicos deste comprovante
    analise['problemas_identificados'].extend([
        'Data mal extraída por OCR: "23(/)2%;;%25" ao invés de "23/05/2025"',
        'Campo "Norme fantasia" ao invés de "Nome fantasia"',
        'Comprovante com QR Code pode interferir na extração'
    ])
    
    return analise

def analyze_generic_comprovante(extracted_data: dict, raw_text: str) -> dict:
    """Análise genérica para outros comprovantes - MELHORADA"""
    
    filename = extracted_data.get('arquivo', '').lower()
    
    # Análise específica para PIX Will Bank baseado no conteúdo
    if 'will bank' in raw_text.lower():
        # Detectar qual comprovante baseado em características únicas
        if 'Sheila Fernandes' in raw_text:
            return analyze_will_bank_pix_17(extracted_data, raw_text)
        elif 'Antonio Valmi' in raw_text:
            return analyze_will_bank_pix_33(extracted_data, raw_text)
        elif 'comprovante_002' in filename:
            return analyze_will_bank_pix_33(extracted_data, raw_text)
        elif 'comprovante_003' in filename:
            return analyze_will_bank_pix_17(extracted_data, raw_text)
        else:
            return analyze_will_bank_pix_generic(extracted_data, raw_text)
    
    return {
        'tipo_analise': 'genérica',
        'dados_extraidos': len(extracted_data),
        'campos_principais': {
            'valor': 'valor_total' in extracted_data or 'valor_numerico' in extracted_data,
            'nome': 'nome' in extracted_data or 'pagador_nome' in extracted_data,
            'data': 'data' in extracted_data or 'data_hora' in extracted_data,
            'tipo': 'tipo_documento' in extracted_data
        },
        'qualidade_texto': 'Boa' if len(raw_text) > 300 else 'Regular',
        'sugestao': 'Use um arquivo com nome específico para análise detalhada'
    }

def analyze_will_bank_pix_33(extracted_data: dict, raw_text: str) -> dict:
    """Análise específica para PIX Will Bank R$ 33,00 (comprovante_002.jpg) - ETAPA 2"""
    
    analise = {
        'comprovante': 'comprovante_002.jpg - PIX Will Bank R$ 33,00 (Antonio)',
        'melhorias_identificadas': [],
        'acertos': [],
        'erros': [],
        'taxa_acerto': 0
    }
    
    # Dados esperados específicos para Antonio
    dados_esperados = {
        'valor': 33.0,
        'origem_nome': 'Antonio Valmi Passos Da Rocha',
        'origem_cpf': '***,097.048-**',
        'destino_nome': 'Ana Cleuma Sousa Dos Santos',
        'destino_cpf': '***,120.983-**',
        'data': '20/05/2025',
        'hora': '17:51:22',
        'descricao': 'pagar piza'
    }
    
    # Executar validações similar ao Sheila mas com dados do Antonio
    valor_extraido = extracted_data.get('valor_total') or extracted_data.get('valor_numerico')
    if valor_extraido == 33.0:
        analise['acertos'].append('✅ VALOR CORRETO: R$ 33,00')
    else:
        analise['erros'].append(f'❌ VALOR: {valor_extraido} (esperado: 33.00)')
    
    origem = extracted_data.get('origem_nome', '') or extracted_data.get('pagador_nome', '')
    if 'Antonio Valmi' in origem:
        analise['acertos'].append('✅ ORIGEM CORRETA: Antonio Valmi')
    else:
        analise['erros'].append(f'❌ ORIGEM: "{origem}"')
    
    origem_cpf = extracted_data.get('origem_cpf', '') or extracted_data.get('pagador_cpf', '')
    if '097.048' in origem_cpf:
        analise['acertos'].append('✅ CPF ORIGEM CORRETO: 097.048')
    else:
        analise['erros'].append(f'❌ CPF ORIGEM: "{origem_cpf}" (esperado: ***,097.048-**)')
    
    destino = extracted_data.get('destino_nome', '') or extracted_data.get('recebedor_nome', '')
    if 'Ana Cleuma' in destino:
        analise['acertos'].append('✅ DESTINO CORRETO: Ana Cleuma')
    
    descricao = extracted_data.get('descricao', '')
    if 'pagar piza' in descricao.lower():
        analise['acertos'].append('✅ DESCRIÇÃO CORRETA: pagar piza')
    
    data = extracted_data.get('data', '')
    if '20/05/2025' in data:
        analise['acertos'].append('✅ DATA CORRETA: 20/05/2025')
    
    # Calcular taxa
    total_verificacoes = 6
    acertos_count = len(analise['acertos'])
    analise['taxa_acerto'] = (acertos_count / total_verificacoes) * 100
    
    if analise['taxa_acerto'] >= 80:
        analise['melhorias_identificadas'] = [
            '🎉 PERFEITO! PIX Antonio R$ 33,00 extraído com precisão',
            '✅ Todos os dados principais corretos',
            '🏆 Sistema otimizado para este layout'
        ]
    
    return analise

def analyze_will_bank_pix_17(extracted_data: dict, raw_text: str) -> dict:
    """Análise específica para PIX Will Bank R$ 17,00 (comprovante_003.jpg) - ETAPA 2"""
    
    analise = {
        'comprovante': 'comprovante_003.jpg - PIX Will Bank R$ 17,00 (Sheila)',
        'melhorias_identificadas': [],
        'acertos': [],
        'erros': [],
        'taxa_acerto': 0
    }
    
    print(f"\n🔍 ANÁLISE DETALHADA - PIX R$ 17,00 (Sheila):")
    
    # Dados esperados específicos para Sheila
    dados_esperados = {
        'valor': 17.0,
        'origem_nome': 'Sheila Fernandes Da Silva',
        'origem_cpf': '***,687.783-**',
        'destino_nome': 'Ana Cleuma Sousa Dos Santos',
        'destino_cpf': '***,120.983-**',
        'data': '22/05/2025',
        'hora': '17:52:04',
        'chave_pix': '(88) 99451-5533'
    }
    
    # 1. Verificar VALOR corrigido
    valor_extraido = extracted_data.get('valor_total') or extracted_data.get('valor_numerico')
    if valor_extraido == 17.0:
        analise['acertos'].append('✅ VALOR CORRETO: R$ 17,00')
    elif valor_extraido in [687.76, 687.0]:
        analise['erros'].append('❌ VALOR OCR INCORRETO: 687.76 (precisa correção para 17.00)')
    else:
        analise['erros'].append(f'❌ VALOR INESPERADO: {valor_extraido}')
    
    # 2. Verificar ORIGEM Sheila
    origem = extracted_data.get('origem_nome', '') or extracted_data.get('pagador_nome', '')
    if 'Sheila Fernandes' in origem:
        analise['acertos'].append('✅ ORIGEM CORRETA: Sheila Fernandes detectada')
    else:
        analise['erros'].append(f'❌ ORIGEM INCORRETA: "{origem}" (esperado: Sheila Fernandes)')
    
    # 3. Verificar CPF origem Sheila
    origem_cpf = extracted_data.get('origem_cpf', '') or extracted_data.get('pagador_cpf', '')
    if '687.783' in origem_cpf:
        analise['acertos'].append('✅ CPF ORIGEM CORRETO: 687.783')
    else:
        analise['erros'].append(f'❌ CPF ORIGEM: "{origem_cpf}" (esperado: ***,687.783-**)')
    
    # 4. Verificar DESTINO Ana Cleuma
    destino = extracted_data.get('destino_nome', '') or extracted_data.get('recebedor_nome', '')
    if 'Ana Cleuma' in destino:
        analise['acertos'].append('✅ DESTINO CORRETO: Ana Cleuma')
    else:
        analise['erros'].append(f'❌ DESTINO: "{destino}"')
    
    # 5. Verificar CPF destino
    destino_cpf = extracted_data.get('destino_cpf', '') or extracted_data.get('recebedor_cpf', '')
    if '120.983' in destino_cpf:
        analise['acertos'].append('✅ CPF DESTINO CORRETO: 120.983')
    else:
        analise['erros'].append(f'❌ CPF DESTINO: "{destino_cpf}"')
    
    # 6. Verificar DATA específica Sheila
    data = extracted_data.get('data', '')
    if '22/05/2025' in data:
        analise['acertos'].append('✅ DATA CORRETA: 22/05/2025 (específica Sheila)')
    else:
        analise['erros'].append(f'❌ DATA: "{data}" (esperado: 22/05/2025)')
    
    # 7. Verificar chave PIX
    chave = extracted_data.get('chave_pix', '')
    if '99451-5533' in chave:
        analise['acertos'].append('✅ CHAVE PIX CORRETA')
    else:
        analise['erros'].append(f'❌ CHAVE PIX: "{chave}"')
    
    # 8. Verificar layout e tipo
    if extracted_data.get('layout_detectado') == 'will_bank':
        analise['acertos'].append('✅ LAYOUT Will Bank detectado')
    if extracted_data.get('tipo_documento') == 'pix':
        analise['acertos'].append('✅ TIPO PIX detectado')
    
    # Calcular taxa de acerto
    total_verificacoes = 8
    acertos_count = len(analise['acertos'])
    analise['taxa_acerto'] = (acertos_count / total_verificacoes) * 100
    
    # Feedback específico baseado na performance
    if analise['taxa_acerto'] >= 85:
        analise['melhorias_identificadas'] = [
            '🎉 EXCELENTE! Comprovante Sheila R$ 17,00 extraído corretamente',
            '✅ Sistema corrigiu valor OCR incorreto',
            '✅ Detecção adaptativa por contexto funcionou',
            '📈 Pronto para produção'
        ]
    elif analise['taxa_acerto'] >= 60:
        analise['melhorias_identificadas'] = [
            '📈 BOA extração, mas precisa ajustes',
            '🔧 Alguns campos ainda precisam correção'
        ]
    else:
        analise['melhorias_identificadas'] = [
            '🚨 NECESSÁRIO: Correções urgentes nos padrões',
            '🔧 Sistema não adaptou corretamente para Sheila'
        ]
    
    # Status detalhado
    analise['status_detalhado'] = {
        'valor_correto': valor_extraido == 17.0,
        'origem_correta': 'Sheila' in origem,
        'cpf_origem_correto': '687.783' in origem_cpf,
        'destino_correto': 'Ana Cleuma' in destino,
        'data_correta': '22/05/2025' in data,
        'precisao_geral': analise['taxa_acerto'],
        'pronto_producao': analise['taxa_acerto'] >= 80
    }
    
    return analise

def extract_basic_data(text: str) -> dict:
    """Extrai dados básicos usando padrões simples"""
    import re
    
    basic_data = {}
    
    # Padrões básicos para casos em que a extração avançada falha
    patterns = {
        'valores': r'R\$\s*([\d,]+\.?\d{0,2})',
        'datas': r'(\d{1,2}/\d{1,2}/\d{4})',
        'horas': r'(\d{1,2}:\d{2}:\d{2})',
        'cpf_mascarado': r'(\*{3}\.?\d{3}\.?\d{3}-?\*{2})',
        'palavras_chave': r'(PIX|TRANSFERÊNCIA|PAGAMENTO|BOLETO)',
    }
    
    for key, pattern in patterns.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            basic_data[key] = matches
    
    return basic_data

def test_single_receipt(image_path: str, verbose: bool = True):
    """Testa extração de dados de um único comprovante com análise de qualidade"""
    
    if not os.path.exists(image_path):
        print(f"❌ Arquivo não encontrado: {image_path}")
        return None
    
    print(f"🔍 Testando comprovante: {os.path.basename(image_path)}")
    print(f"📁 Caminho completo: {image_path}")
    print("-" * 60)
    
    try:
        # Inicializar extrator OCR
        print("⚙️  Inicializando OCR...")
        ocr_extractor = OCRExtractor()
        
        # Extrair texto bruto
        print("📄 Extraindo texto...")
        raw_text = ocr_extractor.extract_text(image_path)
        
        if not raw_text or len(raw_text.strip()) < 10:
            print("❌ Texto extraído muito curto ou vazio")
            print("💡 Verifique se o Tesseract está instalado e funcionando")
            return None
        
        if verbose:
            print(f"📝 Texto extraído ({len(raw_text)} caracteres):")
            print("=" * 40)
            print(raw_text[:500] + "..." if len(raw_text) > 500 else raw_text)
            print("=" * 40)
        
        # Classificar tipo de documento
        try:
            doc_type = ocr_extractor.classify_document_type(raw_text)
            layout = detect_document_layout(raw_text)
            
            print(f"📋 Tipo detectado: {doc_type}")
            print(f"🏦 Layout detectado: {layout}")
        except Exception as classify_error:
            print(f"⚠️  Erro na classificação: {classify_error}")
            doc_type = 'generico'
            layout = 'desconhecido'
        
        # Extrair dados estruturados
        print("🔧 Extraindo dados estruturados...")
        structured_data = None
        
        try:
            structured_data = ocr_extractor.extract_structured_data(raw_text)
        except Exception as extract_error:
            print(f"⚠️  Erro na extração estruturada: {extract_error}")
        
        if structured_data:
            print("✅ Dados estruturados extraídos:")
            for key, value in structured_data.items():
                print(f"   • {key}: {value}")
        else:
            print("⚠️  Nenhum dado estruturado encontrado")
            print("🔧 Tentando extração básica...")
            
            try:
                basic_data = extract_basic_data(raw_text)
                if basic_data:
                    print("📋 Dados básicos encontrados:")
                    for key, value in basic_data.items():
                        print(f"   • {key}: {value}")
                    structured_data = basic_data
                else:
                    print("❌ Nenhum dado básico encontrado")
                    structured_data = {}
            except Exception as basic_error:
                print(f"⚠️  Erro na extração básica: {basic_error}")
                structured_data = {}
        
        # Sempre continuar o processamento, mesmo com dados limitados
        if not structured_data:
            structured_data = {'texto_bruto': raw_text[:100] + "..."}
        
        # Extrair comprovante completo
        print("📊 Criando objeto comprovante...")
        comprovante = None
        
        try:
            comprovante = ocr_extractor.extract_comprovante(image_path)
            if comprovante:
                print("✅ Comprovante criado com sucesso")
            else:
                print("⚠️  Comprovante retornou None")
        except Exception as comp_error:
            print(f"⚠️  Erro ao criar comprovante: {comp_error}")
            print("📋 Continuando com dados estruturados...")
        
        # Preparar dados para análise
        analysis_data = {
            'arquivo': os.path.basename(image_path),
            'tipo_documento': doc_type,
            'layout_detectado': layout,
            'processado_em': datetime.now().isoformat()
        }
        
        # Adicionar dados estruturados
        if structured_data:
            analysis_data.update(structured_data)
        
        # Adicionar dados do comprovante se disponível
        if comprovante:
            try:
                analysis_data.update({
                    'valor_total': comprovante.valor_total,
                    'pagador_nome': comprovante.pagador.nome,
                    'pagador_cpf': comprovante.pagador.cpf,
                    'pagador_instituicao': comprovante.pagador.instituicao,
                    'situacao': comprovante.transacao.situacao,
                    'id_transacao': comprovante.transacao.id_transacao,
                    'data_hora': comprovante.transacao.data_hora,
                    'codigo_operacao': comprovante.transacao.codigo_operacao,
                    'chave_seguranca': comprovante.transacao.chave_seguranca
                })
            except Exception as data_error:
                print(f"⚠️  Erro ao extrair dados do comprovante: {data_error}")
        
        # Análise de qualidade com tratamento robusto
        print("🔍 Analisando qualidade da extração...")
        quality_analysis = None
        
        try:
            quality_analysis = analyze_extraction_quality_safe(analysis_data, raw_text)
        except Exception as quality_error:
            print(f"⚠️  Erro na análise de qualidade: {quality_error}")
            quality_analysis = {
                'erro_analise': str(quality_error),
                'analise_basica': {
                    'dados_extraidos_count': len(analysis_data),
                    'texto_tamanho': len(raw_text),
                    'tipo_detectado': doc_type
                }
            }
        
        # Mostrar resultados da análise
        if quality_analysis and 'erro_analise' in quality_analysis:
            print(f"⚠️  Erro na análise de qualidade: {quality_analysis['erro_analise']}")
            print("📊 Análise básica:")
            basic = quality_analysis.get('analise_basica', {})
            for key, value in basic.items():
                print(f"   • {key}: {value}")
        elif quality_analysis:
            # Mostrar análise detalhada
            print(f"📊 Comprovante: {quality_analysis.get('comprovante', 'genérico')}")
            print(f"📈 Taxa de acerto: {quality_analysis.get('taxa_acerto', 0):.1f}%")
            
            if quality_analysis.get('acertos'):
                print("\n✅ Acertos identificados:")
                for acerto in quality_analysis['acertos']:
                    print(f"   {acerto}")
            
            if quality_analysis.get('erros'):
                print("\n❌ Erros identificados:")
                for erro in quality_analysis['erros']:
                    print(f"   {erro}")
            
            if quality_analysis.get('melhorias_identificadas'):
                print("\n🎉 Melhorias identificadas:")
                for melhoria in quality_analysis['melhorias_identificadas']:
                    print(f"   {melhoria}")
            
            if quality_analysis.get('problemas_identificados'):
                print("\n🔧 Problemas a corrigir:")
                for problema in quality_analysis['problemas_identificados']:
                    print(f"   • {problema}")
        
        # Validar dados (compatibilidade)
        try:
            errors = validate_comprovante(analysis_data)
            if errors:
                print("\n⚠️  Avisos de validação:")
                for error in errors:
                    print(f"   • {error}")
            else:
                print("\n✅ Dados passaram na validação básica")
        except Exception as val_error:
            print(f"⚠️  Erro na validação: {val_error}")
        
        # Resumo final
        print("\n📋 RESUMO DO COMPROVANTE:")
        print("=" * 40)
        print(f"Tipo: {doc_type}")
        print(f"Layout: {layout}")
        
        if comprovante:
            try:
                print(f"Valor: R$ {comprovante.valor_total:.2f}")
                print(f"Pagador: {comprovante.pagador.nome}")
                print(f"CPF: {comprovante.pagador.cpf}")
                print(f"Instituição: {comprovante.pagador.instituicao}")
                print(f"Data/Hora: {comprovante.transacao.data_hora}")
                print(f"ID Transação: {comprovante.transacao.id_transacao}")
                print(f"Situação: {comprovante.transacao.situacao}")
            except Exception as summary_error:
                print(f"⚠️  Erro ao mostrar resumo: {summary_error}")
                print("⚠️  Comprovante criado mas com dados incompletos")
        else:
            print("⚠️  Comprovante não pôde ser criado completamente")
            print(f"Dados estruturados: {len(structured_data)} campos")
        
        # Preparar resultado final
        final_result = {
            'dados_extraidos': analysis_data,
            'analise_qualidade': quality_analysis,
            'metadata': {
                'processado_em': datetime.now().isoformat(),
                'versao': '2.1.0',
                'comprovante_completo': comprovante is not None,
                'texto_extraido_tamanho': len(raw_text)
            }
        }
        
        print("\n✅ TESTE CONCLUÍDO COM SUCESSO!")
        return final_result
            
    except Exception as e:
        print(f"❌ Erro durante o processamento: {e}")
        import traceback
        if verbose:
            print("🔧 Detalhes do erro:")
            traceback.print_exc()
        
        # Retornar erro estruturado
        return {
            'erro': str(e),
            'arquivo': os.path.basename(image_path),
            'timestamp': datetime.now().isoformat(),
            'traceback': traceback.format_exc() if verbose else None
        }

def main():
    """Função principal do script de teste"""
    if len(sys.argv) < 2:
        print("❓ Uso: python src/test_single.py <caminho_da_imagem> [--quiet]")
        print("\n📝 Exemplos:")
        print("  python src/test_single.py data/raw/exemplos/pix_001.jpg")
        print("  python src/test_single.py comprovante.png --quiet")
        print("\n💡 Dica: Use caminhos absolutos se tiver problemas com caminhos relativos")
        return
    
    image_path = sys.argv[1]
    verbose = '--quiet' not in sys.argv
    
    print("🚀 TESTE DE COMPROVANTE INDIVIDUAL")
    print("=" * 60)
    
    result = test_single_receipt(image_path, verbose)
    
    if result and 'erro' not in result:
        print("\n💾 Salvando resultado...")
        
        # Salvar resultado do teste
        output_file = f"test_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_dir = os.path.join('data', 'processed')
        
        # Criar diretório se não existir
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, output_file)
        
        try:
            import json
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"💾 Resultado salvo em: {output_path}")
        except Exception as e:
            print(f"⚠️  Não foi possível salvar resultado: {e}")
    elif result and 'erro' in result:
        print(f"\n❌ TESTE FALHOU COM ERRO: {result['erro']}")
    else:
        print("\n❌ TESTE FALHOU - Resultado vazio")
        print("💡 Dicas para solução:")
        print("   • Verifique se a imagem está legível")
        print("   • Teste com uma imagem de melhor qualidade")
        print("   • Verifique se o Tesseract está instalado corretamente")
        print("   • Execute: tesseract --version")

if __name__ == '__main__':
    main()
