import pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from typing import List, Dict, Any
import os
import re

class MLModel:
    def __init__(self, model_path: str = 'models/comprovante_classifier.pkl'):
        self.model_path = model_path
        self.model = None
        self.vectorizer = None
        self.is_trained = False

    def load_model(self):
        """Carregar o modelo de machine learning a partir do caminho especificado"""
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    model_data = pickle.load(f)
                    self.model = model_data['model']
                    self.vectorizer = model_data['vectorizer']
                    self.is_trained = True
                print("Modelo carregado com sucesso!")
            else:
                print("Arquivo de modelo não encontrado. Treinando novo modelo...")
                self._initialize_default_model()
        except Exception as e:
            print(f"Erro ao carregar modelo: {e}")
            self._initialize_default_model()

    def _initialize_default_model(self):
        """Inicializa um modelo padrão quando não há modelo salvo"""
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words=None)
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)

    def train_model(self, training_data: List[str], labels: List[str]):
        """Treinar o modelo com os dados fornecidos"""
        if not training_data or not labels:
            print("Dados de treinamento vazios")
            return
        
        try:
            # Vetorizar os textos
            X = self.vectorizer.fit_transform(training_data)
            
            # Dividir dados em treino e teste
            X_train, X_test, y_train, y_test = train_test_split(
                X, labels, test_size=0.2, random_state=42
            )
            
            # Treinar o modelo
            self.model.fit(X_train, y_train)
            
            # Avaliar o modelo
            accuracy = self.model.score(X_test, y_test)
            print(f"Acurácia do modelo: {accuracy:.2f}")
            
            self.is_trained = True
            
        except Exception as e:
            print(f"Erro durante o treinamento: {e}")

    def predict(self, new_data: List[str]) -> List[Dict[str, Any]]:
        """Fazer previsões com novos dados extraídos"""
        if not self.is_trained:
            print("Modelo não treinado. Carregando modelo padrão...")
            self.load_model()
        
        if not new_data:
            return []
        
        try:
            # Se não há modelo treinado, retorna dados básicos
            if not self.model or not self.vectorizer:
                return [{'text': text, 'classification': 'unknown'} for text in new_data]
            
            # Vetorizar novos dados
            X_new = self.vectorizer.transform(new_data)
            
            # Fazer predições
            predictions = self.model.predict(X_new)
            probabilities = self.model.predict_proba(X_new)
            
            results = []
            for i, (text, pred) in enumerate(zip(new_data, predictions)):
                result = {
                    'text': text,
                    'classification': pred,
                    'confidence': float(np.max(probabilities[i])),
                    'processed_at': self._get_timestamp()
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            print(f"Erro durante a predição: {e}")
            return [{'text': text, 'classification': 'error', 'error': str(e)} for text in new_data]

    def save_model(self):
        """Salvar o modelo treinado no caminho especificado"""
        try:
            # Criar diretório se não existir
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            
            model_data = {
                'model': self.model,
                'vectorizer': self.vectorizer,
                'trained_at': self._get_timestamp()
            }
            
            with open(self.model_path, 'wb') as f:
                pickle.dump(model_data, f)
            
            print(f"Modelo salvo em: {self.model_path}")
            
        except Exception as e:
            print(f"Erro ao salvar modelo: {e}")

    def classify_document_type(self, text: str) -> str:
        """Classifica o tipo de documento baseado no texto - MELHORADO ETAPA 2"""
        text_lower = text.lower()
        
        # Detecção específica Will Bank PIX
        if 'will bank' in text_lower:
            if any(indicator in text_lower for indicator in ['para', 'de', 'chave', 'autenticação']):
                return 'PIX Will Bank'
        
        # Detecção específica Nubank transferência
        elif 'nu pagamentos' in text_lower or 'nubank' in text_lower:
            if 'transferência' in text_lower or 'destino' in text_lower:
                return 'Transferência Nubank'
            elif 'pix' in text_lower:
                return 'PIX Nubank'
        
        # Detecção PIX genérico
        elif any(indicator in text_lower for indicator in [
            'pix enviado', 'pix recebido', 'comprovante pix', 'comprovante de pix',
            'dados do recebedor', 'dados do pagador', 'chave pix'
        ]):
            return 'PIX Genérico'
        
        # Outros tipos
        elif 'transferência' in text_lower or 'transferencia' in text_lower:
            return 'Transferência Genérica'
        elif 'boleto' in text_lower or 'cobrança' in text_lower:
            return 'Boleto'
        else:
            return 'Comprovante Genérico'

    def predict_with_confidence(self, texts: List[str]) -> List[Dict[str, any]]:
        """Predição com score de confiança melhorado"""
        if not texts:
            return []
        
        results = []
        for text in texts:
            # Classificação baseada em regras (mais confiável para nossos tipos)
            rule_based_type = self.classify_document_type(text)
            
            # Calcular confiança baseada em padrões detectados
            confidence = self._calculate_pattern_confidence(text, rule_based_type)
            
            result = {
                'text_preview': text[:100] + "..." if len(text) > 100 else text,
                'classification': rule_based_type,
                'confidence': confidence,
                'detected_patterns': self._extract_key_patterns(text),
                'processed_at': self._get_timestamp()
            }
            results.append(result)
        
        return results

    def _calculate_pattern_confidence(self, text: str, classification: str) -> float:
        """Calcula confiança baseada em padrões específicos"""
        text_lower = text.lower()
        
        # Padrões por tipo de documento
        pattern_weights = {
            'PIX Will Bank': {
                'will bank': 0.3,
                'para': 0.1,
                'de': 0.1,
                'autenticação': 0.2,
                'chave': 0.1,
                'ana cleuma': 0.2
            },
            'Transferência Nubank': {
                'nu pagamentos': 0.3,
                'transferência': 0.2,
                'destino': 0.15,
                'origem': 0.15,
                'cnpj': 0.1,
                'agência': 0.1
            }
        }
        
        if classification in pattern_weights:
            confidence = 0.0
            for pattern, weight in pattern_weights[classification].items():
                if pattern in text_lower:
                    confidence += weight
            return min(confidence, 1.0)
        
        return 0.5  # Confiança padrão

    def _extract_key_patterns(self, text: str) -> List[str]:
        """Extrai padrões-chave do texto"""
        patterns_found = []
        
        # Valores monetários
        if re.search(r'R\$\s*\d+[,.]?\d{0,2}', text):
            patterns_found.append('valor_monetario')
        
        # CPF
        if re.search(r'\*{3}[.,]?\d{3}[.,]?\d{3}-?\*{2}', text):
            patterns_found.append('cpf_mascarado')
        
        # Data
        if re.search(r'\d{2}/\d{2}/\d{4}', text):
            patterns_found.append('data')
        
        # Bancos específicos
        text_lower = text.lower()
        if 'will bank' in text_lower:
            patterns_found.append('will_bank')
        if 'nu pagamentos' in text_lower:
            patterns_found.append('nubank')
        if 'caixa' in text_lower:
            patterns_found.append('caixa')
        
        return patterns_found

    def _get_timestamp(self) -> str:
        """Retorna timestamp atual"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def load_chatbot_model(self, model_path: str = 'models/chatbot_model.pkl'):
        """Carrega modelo otimizado para chatbot"""
        try:
            if os.path.exists(model_path):
                with open(model_path, 'rb') as f:
                    model_data = pickle.load(f)
                    
                self.chatbot_classifier = model_data.get('intent_classifier')
                self.entity_extractor = model_data.get('entity_extractor')
                self.entity_patterns = model_data.get('entity_patterns', {})
                self.is_chatbot_ready = True
                
                print("✅ Modelo chatbot carregado com sucesso!")
                return True
            else:
                print("⚠️ Modelo chatbot não encontrado. Use o modelo padrão.")
                return False
        except Exception as e:
            print(f"❌ Erro ao carregar modelo chatbot: {e}")
            return False

    def predict_intent(self, user_query: str) -> Dict[str, Any]:
        """Prediz intenção do usuário para o chatbot"""
        if not hasattr(self, 'chatbot_classifier') or not self.chatbot_classifier:
            return {
                'intent': 'unknown',
                'confidence': 0.0,
                'entities': [],
                'suggestion': 'Modelo chatbot não disponível'
            }
        
        try:
            # Extrair features da consulta
            query_features = self.entity_extractor.transform([user_query.lower()])
            
            # Predizer intenção
            intent = self.chatbot_classifier.predict(query_features)[0]
            confidence = max(self.chatbot_classifier.predict_proba(query_features)[0])
            
            # Extrair entidades
            entities = self._extract_entities_from_query(user_query)
            
            # Sugerir ações
            suggestions = self._generate_suggestions(intent, entities)
            
            return {
                'intent': intent,
                'confidence': float(confidence),
                'entities': entities,
                'suggestions': suggestions,
                'processed_at': self._get_timestamp()
            }
            
        except Exception as e:
            return {
                'intent': 'error',
                'confidence': 0.0,
                'entities': [],
                'error': str(e)
            }

    def _extract_entities_from_query(self, query: str) -> List[Dict]:
        """Extrai entidades da consulta do usuário"""
        entities = []
        query_lower = query.lower()
        
        # Extrair valores
        valor_patterns = [r'r\$?\s*(\d+[,.]?\d{0,2})', r'(\d+)\s*reais?']
        for pattern in valor_patterns:
            matches = re.findall(pattern, query_lower)
            for match in matches:
                try:
                    valor = float(match.replace(',', '.'))
                    entities.append({
                        'type': 'valor',
                        'value': valor,
                        'text': match,
                        'confidence': 0.9
                    })
                except:
                    continue
        
        # Extrair nomes conhecidos
        if hasattr(self, 'entity_patterns'):
            for nome in self.entity_patterns.get('destinatarios_frequentes', []):
                if nome.lower() in query_lower:
                    entities.append({
                        'type': 'destinatario',
                        'value': nome,
                        'text': nome,
                        'confidence': 0.95
                    })
        
        # Extrair datas
        data_patterns = [r'(\d{1,2}/\d{1,2}/\d{4})', r'(ontem|hoje|amanhã)']
        for pattern in data_patterns:
            matches = re.findall(pattern, query_lower)
            for match in matches:
                entities.append({
                    'type': 'data',
                    'value': match,
                    'text': match,
                    'confidence': 0.8
                })
        
        return entities

    def _generate_suggestions(self, intent: str, entities: List[Dict]) -> List[str]:
        """Gera sugestões baseadas na intenção e entidades"""
        suggestions = []
        
        if intent == 'busca_por_valor':
            if entities:
                valor = next((e['value'] for e in entities if e['type'] == 'valor'), None)
                if valor:
                    suggestions.append(f"Buscar todas as transações de R$ {valor:.2f}")
                    suggestions.append(f"Histórico de pagamentos no valor de R$ {valor:.2f}")
            else:
                suggestions.append("Especifique o valor que deseja buscar")
        
        elif intent == 'busca_por_destinatario':
            if entities:
                nome = next((e['value'] for e in entities if e['type'] == 'destinatario'), None)
                if nome:
                    suggestions.append(f"Mostrar todos os pagamentos para {nome}")
                    suggestions.append(f"Calcular total enviado para {nome}")
            else:
                suggestions.append("Especifique para quem deseja buscar pagamentos")
        
        elif intent == 'busca_por_data':
            suggestions.append("Mostrar transações do período especificado")
            suggestions.append("Relatório financeiro da data")
        
        elif intent == 'busca_combinada':
            suggestions.append("Busca detalhada com múltiplos critérios")
            suggestions.append("Relatório personalizado")
        
        else:
            suggestions.append("Tente: 'pagamentos para Ana Cleuma'")
            suggestions.append("Tente: 'transações de R$ 33'")
            suggestions.append("Tente: 'histórico Will Bank'")
        
        return suggestions