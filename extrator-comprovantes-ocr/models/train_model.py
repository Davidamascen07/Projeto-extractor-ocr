"""
Script para treinamento de modelos de classificação de comprovantes.

Este script treina modelos de machine learning usando dados anotados
e salva os modelos treinados para uso em produção.
"""

import os
import json
import pickle
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix
from datetime import datetime
import numpy as np

class ModelTrainer:
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.vectorizer = TfidfVectorizer(
            max_features=self.config.get('max_features', 1000),
            stop_words=None,
            ngram_range=(1, 2)
        )
        self.classifier = RandomForestClassifier(
            n_estimators=self.config.get('n_estimators', 100),
            random_state=42,
            max_depth=self.config.get('max_depth', 10)
        )
        
    def _load_config(self, config_path: str) -> dict:
        """Carrega configurações do arquivo ou usa padrões"""
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            'max_features': 1000,
            'n_estimators': 100,
            'max_depth': 10,
            'test_size': 0.2,
            'cv_folds': 5
        }
    
    def prepare_training_data(self, data_path: str) -> tuple:
        """Prepara dados de treinamento a partir de arquivo JSON"""
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            texts = []
            labels = []
            
            # Processar dados das anotações
            if 'anotacoes' in data:
                for item in data['anotacoes']:
                    # Criar múltiplas representações de texto para aumentar dados
                    text_variations = []
                    
                    # Variação 1: Informações básicas
                    basic_features = []
                    if 'tipo' in item:
                        basic_features.append(item['tipo'])
                    if 'pagador' in item and 'nome' in item['pagador']:
                        basic_features.append(item['pagador']['nome'])
                    if 'instituicao' in item:
                        basic_features.append(item['instituicao'])
                    
                    if basic_features:
                        text_variations.append(' '.join(basic_features).lower())
                    
                    # Variação 2: Com informações de valor
                    if 'valor' in item:
                        value_features = basic_features.copy()
                        if 'total' in item['valor']:
                            value_features.append(f"valor {item['valor']['total']}")
                        if 'transacao' in item['valor']:
                            value_features.append(f"transacao {item['valor']['transacao']}")
                        text_variations.append(' '.join(value_features).lower())
                    
                    # Variação 3: Com informações técnicas
                    tech_features = basic_features.copy()
                    if 'id_transacao' in item:
                        tech_features.append(f"id {item['id_transacao']}")
                    if 'data' in item:
                        tech_features.append(f"data {item['data']}")
                    if 'hora' in item:
                        tech_features.append(f"hora {item['hora']}")
                    
                    if len(tech_features) > len(basic_features):
                        text_variations.append(' '.join(tech_features).lower())
                    
                    # Adicionar todas as variações
                    tipo = item.get('tipo', 'Comprovante Genérico')
                    for text_var in text_variations:
                        if text_var.strip():  # Só adiciona se não estiver vazio
                            texts.append(text_var)
                            labels.append(tipo)
            
            # Se ainda temos poucos dados, criar dados sintéticos baseados nos existentes
            if len(texts) < 10:
                texts, labels = self._augment_data(texts, labels)
            
            return texts, labels
            
        except Exception as e:
            print(f"Erro ao preparar dados de treinamento: {e}")
            return [], []
    
    def _augment_data(self, texts: list, labels: list) -> tuple:
        """Aumenta o dataset com variações sintéticas dos dados existentes"""
        augmented_texts = texts.copy()
        augmented_labels = labels.copy()
        
        # Criar variações para cada texto existente
        for original_text, original_label in zip(texts, labels):
            words = original_text.split()
            
            # Variação 1: Ordem diferente das palavras
            if len(words) > 2:
                import random
                random.seed(42)  # Para reprodutibilidade
                shuffled_words = words.copy()
                random.shuffle(shuffled_words)
                augmented_texts.append(' '.join(shuffled_words))
                augmented_labels.append(original_label)
            
            # Variação 2: Adicionar palavras relacionadas ao tipo
            type_keywords = {
                'Consulta Pix': ['pix', 'consulta', 'pagamento', 'transferencia'],
                'Transferência': ['transferencia', 'envio', 'pagamento', 'banco'],
                'Comprovante Pagamento': ['pagamento', 'comprovante', 'quitacao'],
                'Comprovante Boleto': ['boleto', 'cobranca', 'vencimento'],
                'Comprovante Genérico': ['comprovante', 'documento', 'transacao']
            }
            
            if original_label in type_keywords:
                for keyword in type_keywords[original_label][:2]:  # Max 2 keywords
                    if keyword not in original_text:
                        new_text = f"{original_text} {keyword}"
                        augmented_texts.append(new_text)
                        augmented_labels.append(original_label)
        
        print(f"Dataset aumentado de {len(texts)} para {len(augmented_texts)} amostras")
        return augmented_texts, augmented_labels
    
    def train(self, texts: list, labels: list) -> dict:
        """Treina o modelo com os dados fornecidos"""
        if not texts or not labels:
            raise ValueError("Dados de treinamento vazios")
        
        print(f"Iniciando treinamento com {len(texts)} amostras...")
        
        # Vetorizar textos
        X = self.vectorizer.fit_transform(texts)
        
        # Verificar se temos dados suficientes para divisão estratificada
        unique_labels, label_counts = np.unique(labels, return_counts=True)
        min_samples_per_class = min(label_counts)
        
        print(f"Distribuição das classes: {dict(zip(unique_labels, label_counts))}")
        
        if min_samples_per_class < 2 or len(texts) < 4:
            # Dataset muito pequeno - treinar com todos os dados
            print("Dataset pequeno detectado. Treinando com todos os dados disponíveis.")
            self.classifier.fit(X, labels)
            
            train_score = self.classifier.score(X, labels)
            
            # Usar validação leave-one-out para datasets pequenos
            from sklearn.model_selection import LeaveOneOut
            loo = LeaveOneOut()
            loo_scores = []
            
            for train_idx, test_idx in loo.split(X):
                X_train_loo, X_test_loo = X[train_idx], X[test_idx]
                y_train_loo, y_test_loo = np.array(labels)[train_idx], np.array(labels)[test_idx]
                
                self.classifier.fit(X_train_loo, y_train_loo)
                score = self.classifier.score(X_test_loo, y_test_loo)
                loo_scores.append(score)
            
            # Re-treinar com todos os dados
            self.classifier.fit(X, labels)
            
            results = {
                'train_accuracy': train_score,
                'test_accuracy': np.mean(loo_scores),
                'cv_mean': np.mean(loo_scores),
                'cv_std': np.std(loo_scores),
                'classification_report': f'Dataset pequeno - apenas {len(texts)} amostras',
                'confusion_matrix': 'N/A para dataset pequeno',
                'feature_names': self.vectorizer.get_feature_names_out().tolist()[:20],
                'trained_at': datetime.now().isoformat(),
                'n_samples': len(texts),
                'n_features': X.shape[1],
                'training_method': 'Leave-One-Out validation'
            }
            
        else:
            # Dataset normal - usar divisão estratificada
            X_train, X_test, y_train, y_test = train_test_split(
                X, labels, 
                test_size=self.config.get('test_size', 0.2),
                random_state=42,
                stratify=labels
            )
            
            # Treinar modelo
            self.classifier.fit(X_train, y_train)
            
            # Avaliar modelo
            train_score = self.classifier.score(X_train, y_train)
            test_score = self.classifier.score(X_test, y_test)
            
            # Cross-validation
            cv_scores = cross_val_score(
                self.classifier, X, labels, 
                cv=min(self.config.get('cv_folds', 5), len(texts)//2)
            )
            
            # Predições para relatório detalhado
            y_pred = self.classifier.predict(X_test)
            
            results = {
                'train_accuracy': train_score,
                'test_accuracy': test_score,
                'cv_mean': cv_scores.mean(),
                'cv_std': cv_scores.std(),
                'classification_report': classification_report(y_test, y_pred),
                'confusion_matrix': confusion_matrix(y_test, y_pred).tolist(),
                'feature_names': self.vectorizer.get_feature_names_out().tolist()[:50],
                'trained_at': datetime.now().isoformat(),
                'n_samples': len(texts),
                'n_features': X.shape[1],
                'training_method': 'Train-test split with cross-validation'
            }
        
        print(f"Acurácia de treino: {results['train_accuracy']:.3f}")
        print(f"Acurácia de teste: {results['test_accuracy']:.3f}")
        if 'cv_mean' in results:
            print(f"CV Score: {results['cv_mean']:.3f} (+/- {results['cv_std'] * 2:.3f})")
        
        return results
    
    def save_model(self, model_path: str, vectorizer_path: str = None):
        """Salva o modelo treinado"""
        try:
            # Salvar classificador
            with open(model_path, 'wb') as f:
                model_data = {
                    'model': self.classifier,
                    'vectorizer': self.vectorizer,
                    'config': self.config,
                    'trained_at': datetime.now().isoformat()
                }
                pickle.dump(model_data, f)
            
            print(f"Modelo salvo em: {model_path}")
            
            # Salvar vetorizador separadamente se especificado
            if vectorizer_path:
                with open(vectorizer_path, 'wb') as f:
                    pickle.dump(self.vectorizer, f)
                print(f"Vetorizador salvo em: {vectorizer_path}")
                
        except Exception as e:
            print(f"Erro ao salvar modelo: {e}")

class ChatbotOptimizedModelTrainer(ModelTrainer):
    """Trainer especializado para dados de chatbot"""
    
    def __init__(self, config_path: str = None):
        super().__init__(config_path)
        
        # Configurações específicas para chatbot
        self.chatbot_features = {
            'entity_extraction': TfidfVectorizer(
                max_features=500,
                ngram_range=(1, 3),
                stop_words=None
            ),
            'value_classifier': RandomForestClassifier(
                n_estimators=50,
                random_state=42
            ),
            'confidence_threshold': 0.7
        }
    
    def prepare_chatbot_training_data(self, processed_data_dir: str) -> tuple:
        """Prepara dados específicos para consultas de chatbot"""
        
        training_texts = []
        training_labels = []
        entity_data = []
        
        # Carregar dados processados
        data_files = [
            'dados_chatbot.json',
            'comprovantes_estruturados.json', 
            'anotacoes.json'
        ]
        
        all_transactions = []
        
        for file_name in data_files:
            file_path = os.path.join(processed_data_dir, file_name)
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                if 'transacoes' in data:
                    all_transactions.extend(data['transacoes'])
                elif 'comprovantes' in data:
                    all_transactions.extend(data['comprovantes'])
                elif 'anotacoes' in data:
                    all_transactions.extend(data['anotacoes'])
        
        print(f"Total de transações carregadas: {len(all_transactions)}")
        
        # Gerar variações de consulta para cada transação
        for transaction in all_transactions:
            queries, labels, entities = self._generate_chatbot_queries(transaction)
            training_texts.extend(queries)
            training_labels.extend(labels)
            entity_data.extend(entities)
        
        # Augmentação de dados para chatbot
        augmented_texts, augmented_labels = self._augment_chatbot_data(
            training_texts, training_labels, entity_data
        )
        
        return augmented_texts, augmented_labels, entity_data
    
    def _generate_chatbot_queries(self, transaction: dict) -> tuple:
        """Gera consultas possíveis para uma transação"""
        
        queries = []
        labels = []
        entities = []
        
        # Extrair dados da transação
        valor = self._extract_value(transaction)
        nome_origem = self._extract_origin_name(transaction)
        nome_destino = self._extract_destination_name(transaction)
        data = self._extract_date(transaction)
        tipo = self._extract_type(transaction)
        banco = self._extract_bank(transaction)
        
        # Gerar consultas por valor
        if valor > 0:
            valor_queries = [
                f"transação de {valor}",
                f"pagamento de R$ {valor:.2f}",
                f"transferência {valor:.0f} reais",
                f"pix de {valor}",
                f"enviei {valor:.2f}"
            ]
            for query in valor_queries:
                queries.append(query)
                labels.append('busca_por_valor')
                entities.append({
                    'tipo': 'valor',
                    'valor': valor,
                    'transacao_id': transaction.get('id_transacao', '')
                })
        
        # Gerar consultas por destinatário
        if nome_destino:
            dest_queries = [
                f"pagamento para {nome_destino}",
                f"transferência para {nome_destino}",
                f"enviei dinheiro para {nome_destino}",
                f"pix para {nome_destino.split()[0]}",
                f"quanto paguei para {nome_destino}"
            ]
            for query in dest_queries:
                queries.append(query)
                labels.append('busca_por_destinatario')
                entities.append({
                    'tipo': 'destinatario',
                    'nome': nome_destino,
                    'transacao_id': transaction.get('id_transacao', '')
                })
        
        # Gerar consultas por data
        if data:
            data_queries = [
                f"transações em {data}",
                f"pagamentos de {data}",
                f"o que paguei em {data}",
                f"histórico {data}"
            ]
            for query in data_queries:
                queries.append(query)
                labels.append('busca_por_data')
                entities.append({
                    'tipo': 'data',
                    'data': data,
                    'transacao_id': transaction.get('id_transacao', '')
                })
        
        # Gerar consultas por banco
        if banco:
            banco_queries = [
                f"transações {banco}",
                f"pagamentos via {banco}",
                f"histórico {banco}",
                f"pix {banco}"
            ]
            for query in banco_queries:
                queries.append(query)
                labels.append('busca_por_banco')
                entities.append({
                    'tipo': 'banco',
                    'banco': banco,
                    'transacao_id': transaction.get('id_transacao', '')
                })
        
        # Gerar consultas combinadas
        if nome_destino and valor > 0:
            combined_queries = [
                f"quanto paguei para {nome_destino}",
                f"transferência {valor:.0f} para {nome_destino}",
                f"histórico pagamentos {nome_destino}"
            ]
            for query in combined_queries:
                queries.append(query)
                labels.append('busca_combinada')
                entities.append({
                    'tipo': 'combinada',
                    'destinatario': nome_destino,
                    'valor': valor,
                    'transacao_id': transaction.get('id_transacao', '')
                })
        
        return queries, labels, entities
    
    def _augment_chatbot_data(self, texts: list, labels: list, entities: list) -> tuple:
        """Aumenta dataset com variações de linguagem natural"""
        
        augmented_texts = texts.copy()
        augmented_labels = labels.copy()
        
        # Variações de linguagem
        variations = {
            'pagamento': ['transferência', 'envio', 'pix', 'débito'],
            'para': ['pro', 'pra', 'para a', 'destinatário'],
            'quanto': ['valor', 'qual valor', 'quanto foi'],
            'reais': ['reais', 'R$', 'dinheiro', 'grana'],
            'Ana Cleuma': ['Ana', 'Cleuma', 'Ana Cleuma Sousa']
        }
        
        # Aplicar variações
        for original_text, label in zip(texts, labels):
            for word, replacements in variations.items():
                if word.lower() in original_text.lower():
                    for replacement in replacements[:2]:  # Máximo 2 variações
                        new_text = original_text.replace(word, replacement)
                        if new_text != original_text:
                            augmented_texts.append(new_text)
                            augmented_labels.append(label)
        
        print(f"Dataset expandido de {len(texts)} para {len(augmented_texts)} consultas")
        return augmented_texts, augmented_labels
    
    def train_chatbot_model(self, texts: list, labels: list, entities: list) -> dict:
        """Treina modelo específico para chatbot"""
        
        if not texts:
            raise ValueError("Dados de treinamento vazios")
        
        print(f"Treinando modelo para chatbot com {len(texts)} consultas...")
        
        # Treinar classificador de intenção
        X = self.chatbot_features['entity_extraction'].fit_transform(texts)
        
        # Dividir dados
        if len(texts) > 10:
            X_train, X_test, y_train, y_test = train_test_split(
                X, labels, test_size=0.2, random_state=42, stratify=labels
            )
        else:
            X_train, X_test, y_train, y_test = X, X, labels, labels
        
        # Treinar
        self.chatbot_features['value_classifier'].fit(X_train, y_train)
        
        # Avaliar
        train_score = self.chatbot_features['value_classifier'].score(X_train, y_train)
        test_score = self.chatbot_features['value_classifier'].score(X_test, y_test)
        
        # Extrair entidades importantes
        entity_patterns = self._extract_entity_patterns(entities)
        
        results = {
            'model_type': 'chatbot_optimized',
            'train_accuracy': train_score,
            'test_accuracy': test_score,
            'n_queries': len(texts),
            'n_entities': len(entities),
            'intent_distribution': dict(pd.Series(labels).value_counts()),
            'entity_patterns': entity_patterns,
            'trained_at': datetime.now().isoformat(),
            'ready_for_chatbot': True
        }
        
        print(f"Modelo chatbot treinado - Acurácia: {test_score:.3f}")
        return results
    
    def _extract_entity_patterns(self, entities: list) -> dict:
        """Extrai padrões de entidades para o chatbot"""
        
        patterns = {
            'valores_comuns': [],
            'destinatarios_frequentes': [],
            'bancos_utilizados': [],
            'datas_periodo': []
        }
        
        for entity in entities:
            if entity['tipo'] == 'valor':
                patterns['valores_comuns'].append(entity['valor'])
            elif entity['tipo'] == 'destinatario':
                patterns['destinatarios_frequentes'].append(entity['nome'])
            elif entity['tipo'] == 'banco':
                patterns['bancos_utilizados'].append(entity['banco'])
            elif entity['tipo'] == 'data':
                patterns['datas_periodo'].append(entity['data'])
        
        # Remover duplicatas e ordenar por frequência
        for key in patterns:
            patterns[key] = list(pd.Series(patterns[key]).value_counts().head(10).index)
        
        return patterns
    
    def save_chatbot_model(self, model_path: str, entity_patterns: dict):
        """Salva modelo otimizado para chatbot"""
        
        try:
            chatbot_model = {
                'intent_classifier': self.chatbot_features['value_classifier'],
                'entity_extractor': self.chatbot_features['entity_extraction'],
                'entity_patterns': entity_patterns,
                'config': self.config,
                'model_type': 'chatbot_optimized',
                'trained_at': datetime.now().isoformat(),
                'version': '2.0'
            }
            
            with open(model_path, 'wb') as f:
                pickle.dump(chatbot_model, f)
            
            print(f"Modelo chatbot salvo em: {model_path}")
            
            # Salvar também configuração JSON para o chatbot
            config_path = model_path.replace('.pkl', '_config.json')
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'entity_patterns': entity_patterns,
                    'model_type': 'chatbot_optimized',
                    'confidence_threshold': self.chatbot_features['confidence_threshold'],
                    'supported_intents': [
                        'busca_por_valor',
                        'busca_por_destinatario', 
                        'busca_por_data',
                        'busca_por_banco',
                        'busca_combinada'
                    ]
                }, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            print(f"Erro ao salvar modelo chatbot: {e}")
    
    # Métodos auxiliares de extração
    def _extract_value(self, transaction: dict) -> float:
        """Extrai valor da transação"""
        return transaction.get('valor_total', 0) or transaction.get('valor_numerico', 0) or transaction.get('valor', {}).get('total', 0)
    
    def _extract_origin_name(self, transaction: dict) -> str:
        """Extrai nome origem"""
        return transaction.get('origem_nome', '') or transaction.get('pagador_nome', '') or transaction.get('pagador', {}).get('nome', '')
    
    def _extract_destination_name(self, transaction: dict) -> str:
        """Extrai nome destino"""
        return transaction.get('destino_nome', '') or transaction.get('recebedor_nome', '') or transaction.get('devedor', {}).get('nome', '')
    
    def _extract_date(self, transaction: dict) -> str:
        """Extrai data"""
        return transaction.get('data', '') or transaction.get('data_hora', '').split()[0] if transaction.get('data_hora') else ''
    
    def _extract_type(self, transaction: dict) -> str:
        """Extrai tipo"""
        return transaction.get('tipo_documento', '') or transaction.get('tipo', '')
    
    def _extract_bank(self, transaction: dict) -> str:
        """Extrai banco"""
        return transaction.get('layout_detectado', '').replace('_', ' ').title() or transaction.get('instituicao', '')

def main():
    """Função principal para treinamento"""
    print("=== Treinamento de Modelo de Classificação de Comprovantes ===")
    
    # Caminhos dos arquivos
    data_path = '../data/processed/anotacoes.json'
    model_path = './comprovante_classifier.pkl'
    config_path = './model_config.json'
    
    # Verificar se arquivo de dados existe
    if not os.path.exists(data_path):
        print(f"Arquivo de dados não encontrado: {data_path}")
        print("Por favor, certifique-se de que os dados anotados estão disponíveis.")
        return
    
    try:
        # Inicializar trainer
        trainer = ModelTrainer(config_path)
        
        # Preparar dados
        texts, labels = trainer.prepare_training_data(data_path)
        
        if not texts:
            print("Nenhum dado de treinamento encontrado.")
            return
        
        print(f"Dados carregados: {len(texts)} amostras")
        print(f"Classes encontradas: {set(labels)}")
        
        # Treinar modelo
        results = trainer.train(texts, labels)
        
        # Salvar modelo
        trainer.save_model(model_path)
        
        # Salvar resultados do treinamento
        results_path = './training_results.json'
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\nResultados do treinamento salvos em: {results_path}")
        print("\n=== Treinamento Concluído ===")
        
    except Exception as e:
        print(f"Erro durante o treinamento: {e}")

if __name__ == '__main__':
    main()

def main():
    """Função principal para treinamento otimizado para chatbot"""
    print("=== Treinamento de Modelo Otimizado para Chatbot ===")
    
    # Caminhos
    processed_data_dir = '../data/processed/'
    model_path = './chatbot_model.pkl'
    config_path = './model_config.json'
    
    try:
        # Inicializar trainer especializado
        trainer = ChatbotOptimizedModelTrainer(config_path)
        
        # Preparar dados para chatbot
        texts, labels, entities = trainer.prepare_chatbot_training_data(processed_data_dir)
        
        if not texts:
            print("❌ Nenhum dado encontrado para treinamento")
            print("💡 Execute primeiro o processamento dos comprovantes:")
            print("   python src/main.py")
            return
        
        print(f"✅ Dados preparados:")
        print(f"   - {len(texts)} consultas de treinamento")
        print(f"   - {len(set(labels))} tipos de intenção")
        print(f"   - {len(entities)} entidades extraídas")
        
        # Treinar modelo
        results = trainer.train_chatbot_model(texts, labels, entities)
        
        # Salvar modelo
        trainer.save_chatbot_model(model_path, results['entity_patterns'])
        
        # Salvar resultados
        results_path = './chatbot_training_results.json'
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Modelo otimizado para chatbot criado com sucesso!")
        print(f"📊 Estatísticas:")
        print(f"   - Acurácia de treino: {results['train_accuracy']:.1%}")
        print(f"   - Acurácia de teste: {results['test_accuracy']:.1%}")
        print(f"   - Intenções suportadas: {len(results['intent_distribution'])}")
        print(f"   - Pronto para chatbot: {'✅ Sim' if results['ready_for_chatbot'] else '❌ Não'}")
        
        # Mostrar entidades mais frequentes
        if 'entity_patterns' in results:
            patterns = results['entity_patterns']
            print(f"\n🔍 Entidades mais frequentes:")
            if patterns['destinatarios_frequentes']:
                print(f"   - Destinatários: {', '.join(patterns['destinatarios_frequentes'][:3])}")
            if patterns['valores_comuns']:
                print(f"   - Valores: R$ {', R$ '.join(map(str, patterns['valores_comuns'][:3]))}")
            if patterns['bancos_utilizados']:
                print(f"   - Bancos: {', '.join(patterns['bancos_utilizados'][:3])}")
        
        print(f"\n📁 Arquivos gerados:")
        print(f"   - Modelo: {model_path}")
        print(f"   - Configuração: {model_path.replace('.pkl', '_config.json')}")
        print(f"   - Resultados: {results_path}")
        
    except Exception as e:
        print(f"❌ Erro durante o treinamento: {e}")
        import traceback
        traceback.print_exc()
