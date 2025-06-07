# Sistema de Extração OCR de Comprovantes

Sistema automatizado para extração de dados de comprovantes financeiros usando OCR e Machine Learning.

## 🚀 Como Executar

### Opção 1: Script Principal (Recomendado)
```bash
# Da raiz do projeto
python run_extraction.py
```

### Opção 2: Módulo diretamente
```bash
# Da raiz do projeto
python -m src.main
```

### Opção 3: Via src/main.py
```bash
# Da raiz do projeto  
python src/main.py
```

## 📁 Estrutura de Arquivos

```
extrator-comprovantes-ocr/
├── run_extraction.py          # Script principal (use este!)
├── src/
│   ├── main.py               # Módulo principal
│   ├── ocr/
│   │   └── extractor.py      # Extração OCR
│   ├── ml/
│   │   └── model.py          # Modelos ML
│   └── utils/
│       └── helpers.py        # Funções auxiliares
├── data/
│   ├── raw/exemplos/         # Coloque suas imagens aqui
│   └── processed/            # Dados processados (gerado automaticamente)
└── models/                   # Modelos treinados
```

## 📝 Dependências

```bash
pip install pytesseract opencv-python scikit-learn pandas
```

## 🎯 Funcionalidades

- ✅ Extração OCR de comprovantes PIX, transferências e boletos
- ✅ Detecção automática de layout (Will Bank, Nubank, Caixa, etc.)
- ✅ Correção automática de erros comuns de OCR
- ✅ Dados estruturados prontos para chatbot
- ✅ Validação de padrões específicos
- ✅ Índices de busca otimizados

## 📊 Dados de Saída

O sistema gera dois arquivos principais:

### `comprovantes_estruturados.json`
Dados brutos extraídos de cada comprovante.

### `dados_chatbot.json`
Dados otimizados para integração com chatbot, incluindo:
- Estrutura padronizada
- Índices de busca
- Metadados de confiabilidade
- Consultas pré-formatadas

## 🤖 Integração com Chatbot

Para treinar o modelo específico para chatbot:

```bash
# Após executar a extração
python models/train_model.py
```

Isso criará um modelo otimizado para responder consultas como:
- "Quanto paguei para Ana Cleuma?"
- "Transações de R$ 33,00"
- "Histórico Will Bank"
- "Pagamentos em maio/2025"