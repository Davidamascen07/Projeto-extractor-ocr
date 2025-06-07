class PIXChatbot {
    constructor() {
        this.apiBaseUrl = 'http://localhost:5000/api';
        this.messagesContainer = document.getElementById('chat-messages');
        this.chatInput = document.getElementById('chat-input');
        this.sendBtn = document.getElementById('send-btn');
        this.attachBtn = document.getElementById('attach-btn');
        this.fileInput = document.getElementById('file-input-chat');
        this.fileUploadArea = document.getElementById('file-upload-area');
        this.typingIndicator = document.getElementById('typing-indicator');
        this.charCount = document.getElementById('char-count');
        this.clearBtn = document.getElementById('clear-chat');
        this.voiceBtn = document.getElementById('voice-btn');
        
        this.currentFile = null;
        this.extractedData = null;
        this.conversationHistory = [];
        this.isTyping = false;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.checkAPIHealth();
        this.loadChatHistory();
    }
    
    setupEventListeners() {
        // Chat input events
        if (this.sendBtn) {
            this.sendBtn.addEventListener('click', () => this.sendMessage());
        }
        
        if (this.chatInput) {
            this.chatInput.addEventListener('keydown', (e) => this.handleKeyDown(e));
            this.chatInput.addEventListener('input', () => this.handleInputChange());
        }
        
        // File upload events
        if (this.attachBtn) {
            this.attachBtn.addEventListener('click', () => this.toggleFileUpload());
        }
        
        if (this.fileInput) {
            this.fileInput.addEventListener('change', (e) => this.handleFileUpload(e));
        }
        
        // Other buttons
        if (this.clearBtn) {
            this.clearBtn.addEventListener('click', () => this.clearChat());
        }
        
        if (this.voiceBtn) {
            this.voiceBtn.addEventListener('click', () => this.toggleVoiceInput());
        }
        
        // Quick actions
        document.querySelectorAll('.quick-action').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const text = e.target.textContent.replace(/[💰📊🔍❓] "(.+)"/, '$1');
                this.chatInput.value = text;
                this.handleInputChange();
                this.sendMessage();
            });
        });
        
        // File drag and drop
        this.setupFileDragDrop();
    }
    
    handleKeyDown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.sendMessage();
        }
    }
    
    handleInputChange() {
        const text = this.chatInput.value;
        const length = text.length;
        
        this.charCount.textContent = `${length}/500`;
        this.sendBtn.disabled = length === 0;
        
        if (length > 500) {
            this.charCount.classList.add('text-red-400');
            this.chatInput.value = text.substring(0, 500);
        } else {
            this.charCount.classList.remove('text-red-400');
        }
        
        // Auto-resize textarea sem mostrar scrollbar
        this.chatInput.style.height = 'auto';
        const newHeight = Math.min(this.chatInput.scrollHeight, 120); // Máximo 120px
        this.chatInput.style.height = newHeight + 'px';
        
        // Garantir que o overflow permaneça hidden
        this.chatInput.style.overflow = 'hidden';
    }
    
    toggleFileUpload() {
        if (!this.fileUploadArea) return;
        
        const isHidden = this.fileUploadArea.classList.contains('hidden');
        if (isHidden) {
            this.fileUploadArea.classList.remove('hidden');
            this.attachBtn.classList.add('text-primary');
        } else {
            this.fileUploadArea.classList.add('hidden');
            this.attachBtn.classList.remove('text-primary');
        }
    }
    
    setupFileDragDrop() {
        if (!this.fileUploadArea) return;
        
        const dropArea = this.fileUploadArea.querySelector('.file-drop-mini');
        if (!dropArea) return;
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        });
        
        ['dragenter', 'dragover'].forEach(eventName => {
            dropArea.addEventListener(eventName, () => {
                dropArea.style.backgroundColor = 'rgba(139, 92, 246, 0.1)';
            });
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, () => {
                dropArea.style.backgroundColor = 'transparent';
            });
        });
        
        dropArea.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            this.handleFiles(files);
        });
        
        dropArea.addEventListener('click', () => {
            this.fileInput.click();
        });
    }
    
    handleFileUpload(e) {
        const files = e.target.files;
        this.handleFiles(files);
    }
    
    handleFiles(files) {
        if (files.length === 0) return;
        
        const file = files[0];
        console.log('Arquivo selecionado no chat:', file.name, file.type, file.size);
        
        if (!this.isValidFileType(file)) {
            this.addMessage('bot', '❌ Por favor, envie apenas arquivos de imagem (JPG, PNG) ou PDF.', null, true);
            return;
        }
        
        if (file.size > 16 * 1024 * 1024) {
            this.addMessage('bot', '❌ Arquivo muito grande. Tamanho máximo: 16MB', null, true);
            return;
        }
        
        this.currentFile = file;
        
        // Add user message with file
        this.addMessage('user', `📎 Enviou: ${file.name}`);
        
        // Hide file upload area
        this.fileUploadArea.classList.add('hidden');
        this.attachBtn.classList.remove('text-primary');
        
        // Clear file input
        this.fileInput.value = '';
        
        // Process file
        this.processFile(file);
    }
    
    isValidFileType(file) {
        const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf'];
        return allowedTypes.includes(file.type.toLowerCase());
    }
    
    async sendMessage() {
        const message = this.chatInput.value.trim();
        if (!message || this.isTyping) return;
        
        // Add user message
        this.addMessage('user', message);
        
        // Clear input
        this.chatInput.value = '';
        this.handleInputChange();
        
        try {
            // Try to send to API first
            const response = await this.sendToAPI(message);
            this.addMessage('bot', response.response, response.data);
        } catch (error) {
            console.warn('API não disponível, usando modo simulado:', error);
            // Fallback to simulated responses
            await this.processMessageSimulated(message);
        }
    }
    
    async sendToAPI(message) {
        const response = await fetch(`${this.apiBaseUrl}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                context: {
                    chat_history: this.conversationHistory.slice(-5),
                    current_file: this.currentFile
                }
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    }
    
    async processMessageSimulated(message) {
        this.showTyping();
        
        // Simulate processing delay
        await this.delay(1500);
        
        let response = '';
        
        // Simple intent recognition
        if (this.isGreeting(message)) {
            response = this.getGreetingResponse();
        } else if (this.isQuestion(message)) {
            response = this.getQuestionResponse(message);
        } else if (this.isValueQuery(message)) {
            response = this.getValueResponse();
        } else if (this.isReportRequest(message)) {
            response = this.getReportResponse();
        } else {
            response = this.getDefaultResponse(message);
        }
        
        this.hideTyping();
        this.addMessage('bot', response);
    }
    
    async processFile(file) {
        this.showTyping();
        
        try {
            // Try to use real API first
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch(`${this.apiBaseUrl}/extract`, {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    this.extractedData = this.convertAPIDataToChat(result.data);
                    const responseText = this.getExtractionResponse();
                    this.hideTyping();
                    this.addMessage('bot', responseText);
                    return;
                }
            }
        } catch (error) {
            console.warn('API não disponível, usando dados simulados:', error);
        }
        
        // Fallback to simulated data
        await this.delay(2500);
        
        // Mock extracted data
        this.extractedData = {
            valor: 'R$ 1.247,90',
            destinatario: 'Maria Fernanda Oliveira Santos',
            cpf: '123.456.789-00',
            remetente: 'Carlos Roberto Silva',
            data: '15/07/2023 14:23',
            transacao: 'PIX9H832FJ73G',
            banco_origem: 'Nu Pagamentos S.A.',
            banco_destino: 'Banco do Brasil'
        };
        
        const response = this.getExtractionResponse();
        
        this.hideTyping();
        this.addMessage('bot', response);
    }
    
    convertAPIDataToChat(apiData) {
        return {
            valor: this.formatCurrency(apiData.valor_total || apiData.valor_numerico || 0),
            destinatario: apiData.destino_nome || apiData.recebedor_nome || 'Não identificado',
            cpf: apiData.destino_cpf || apiData.recebedor_cpf || 'Não identificado',
            remetente: apiData.origem_nome || apiData.pagador_nome || 'Não identificado',
            data: apiData.data_hora || apiData.data || 'Não identificada',
            transacao: apiData.codigo_operacao || apiData.id_transacao || 'Não identificado'
        };
    }
    
    formatCurrency(value) {
        if (typeof value !== 'number') return 'R$ 0,00';
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value);
    }
    
    // Response generators (baseado no backup)
    getExtractionResponse() {
        return `✅ <strong>Comprovante processado com sucesso!</strong>
        
        <div class="extracted-data mt-4 p-4 rounded-lg">
            <h4 class="font-semibold mb-3 text-blue-300">📊 Dados Extraídos:</h4>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                <div><strong>💰 Valor:</strong> ${this.extractedData.valor}</div>
                <div><strong>📅 Data:</strong> ${this.extractedData.data}</div>
                <div><strong>👤 Destinatário:</strong> ${this.extractedData.destinatario}</div>
                <div><strong>📄 CPF:</strong> ${this.extractedData.cpf}</div>
                <div><strong>🏦 Remetente:</strong> ${this.extractedData.remetente}</div>
                <div><strong>🔢 Transação:</strong> ${this.extractedData.transacao}</div>
            </div>
        </div>
        
        Agora você pode me fazer perguntas sobre este comprovante! 🤔`;
    }
    
    getGreetingResponse() {
        const greetings = [
            '👋 Olá! Como posso ajudar com seus comprovantes PIX hoje?',
            '😊 Oi! Pronto para analisar alguns comprovantes?',
            '🎉 Bem-vindo! Vamos começar a extrair dados dos seus PIX?'
        ];
        return greetings[Math.floor(Math.random() * greetings.length)];
    }
    
    getQuestionResponse(message) {
        if (!this.extractedData) {
            return '🤔 Para responder suas perguntas, preciso primeiro analisar um comprovante. Envie um arquivo PIX!';
        }
        
        const lowerMessage = message.toLowerCase();
        
        if (lowerMessage.includes('valor')) {
            return `💰 O valor da transação é <strong>${this.extractedData.valor}</strong>`;
        }
        if (lowerMessage.includes('destinat') || lowerMessage.includes('receb')) {
            return `👤 O destinatário é <strong>${this.extractedData.destinatario}</strong> (CPF: ${this.extractedData.cpf})`;
        }
        if (lowerMessage.includes('data') || lowerMessage.includes('quando')) {
            return `📅 A transação foi realizada em <strong>${this.extractedData.data}</strong>`;
        }
        if (lowerMessage.includes('cpf')) {
            return `📄 O CPF do destinatário é <strong>${this.extractedData.cpf}</strong>`;
        }
        if (lowerMessage.includes('remetente') || lowerMessage.includes('pagador')) {
            return `🏦 O remetente é <strong>${this.extractedData.remetente}</strong>`;
        }
        
        return '🤖 Posso responder sobre: valor, destinatário, data, CPF, remetente. Reformule sua pergunta!';
    }
    
    getValueResponse() {
        if (!this.extractedData) {
            return '💰 Envie um comprovante primeiro para eu analisar os valores!';
        }
        return `💰 O valor total da transação analisada é <strong>${this.extractedData.valor}</strong>`;
    }
    
    getReportResponse() {
        if (!this.extractedData) {
            return '📊 Preciso de pelo menos um comprovante para gerar um relatório!';
        }
        
        return `📊 <strong>Relatório da Transação PIX</strong>
        
        <div class="bg-gray-800 p-4 rounded-lg mt-3 font-mono text-sm">
            =================================<br>
            📄 RELATÓRIO PIX - ${new Date().toLocaleDateString()}<br>
            =================================<br>
            💰 Valor: ${this.extractedData.valor}<br>
            📅 Data: ${this.extractedData.data}<br>
            👤 De: ${this.extractedData.remetente}<br>
            👤 Para: ${this.extractedData.destinatario}<br>
            📄 CPF: ${this.extractedData.cpf}<br>
            🔢 ID: ${this.extractedData.transacao}<br>
            =================================
        </div>`;
    }
    
    getDefaultResponse(message) {
        const responses = [
            '🤖 Interessante! Mas foque em perguntas sobre comprovantes PIX. Como posso ajudar?',
            '💡 Estou aqui para análise de PIX. Envie um comprovante ou faça perguntas específicas!',
            '🎯 Minha especialidade são comprovantes PIX. O que você gostaria de saber?'
        ];
        return responses[Math.floor(Math.random() * responses.length)];
    }
    
    // Utility functions
    isGreeting(message) {
        const greetingWords = ['oi', 'olá', 'hello', 'bom dia', 'boa tarde', 'boa noite'];
        return greetingWords.some(word => message.toLowerCase().includes(word));
    }
    
    isQuestion(message) {
        const questionWords = ['qual', 'como', 'quando', 'onde', 'quem', 'quanto', '?'];
        return questionWords.some(word => message.toLowerCase().includes(word));
    }
    
    isValueQuery(message) {
        const valueWords = ['valor', 'preço', 'quanto', 'dinheiro', 'total'];
        return valueWords.some(word => message.toLowerCase().includes(word));
    }
    
    isReportRequest(message) {
        const reportWords = ['relatório', 'relatorio', 'resumo', 'report'];
        return reportWords.some(word => message.toLowerCase().includes(word));
    }
    
    toggleVoiceInput() {
        if ('speechRecognition' in window || 'webkitSpeechRecognition' in window) {
            this.startVoiceRecognition();
        } else {
            this.addMessage('bot', 'Reconhecimento de voz não é suportado neste navegador.', null, true);
        }
    }
    
    startVoiceRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        
        recognition.lang = 'pt-BR';
        recognition.continuous = false;
        recognition.interimResults = false;
        
        this.voiceBtn.innerHTML = '<i class="fas fa-microphone-slash text-lg animate-pulse"></i>';
        this.voiceBtn.classList.add('text-red-400');
        
        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            this.chatInput.value = transcript;
            this.handleInputChange();
        };
        
        recognition.onerror = (event) => {
            console.error('Erro no reconhecimento de voz:', event.error);
            this.addMessage('bot', 'Erro no reconhecimento de voz. Tente novamente.', null, true);
        };
        
        recognition.onend = () => {
            this.voiceBtn.innerHTML = '<i class="fas fa-microphone text-lg"></i>';
            this.voiceBtn.classList.remove('text-red-400');
        };
        
        recognition.start();
    }
    
    addMessage(sender, content, data = null, isError = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `animate-fade-in ${sender === 'user' ? 'flex justify-end' : ''}`;
        
        if (sender === 'user') {
            messageDiv.innerHTML = `
                <div class="message-user rounded-2xl p-4 max-w-md">
                    <div class="text-white">${this.escapeHtml(content)}</div>
                    <div class="text-xs text-gray-200 mt-2 opacity-70">${new Date().toLocaleTimeString()}</div>
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="message-bot rounded-2xl p-4 max-w-2xl ${isError ? 'bg-red-900 border-red-600' : ''}">
                    <div class="flex items-start">
                        <div class="w-8 h-8 bg-gradient-to-r from-primary to-secondary rounded-full flex items-center justify-center flex-shrink-0">
                            <i class="fas fa-robot text-sm"></i>
                        </div>
                        <div class="ml-3 flex-1">
                            <div class="text-sm text-gray-400 mb-1">Assistente PIX</div>
                            <div class="text-gray-100">${content}</div>
                            <div class="text-xs text-gray-500 mt-2">${new Date().toLocaleTimeString()}</div>
                        </div>
                    </div>
                </div>
            `;
        }
        
        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
        
        // Save to history
        this.conversationHistory.push({ sender, content, timestamp: new Date() });
        this.saveChatHistory();
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    showTyping() {
        this.isTyping = true;
        this.typingIndicator.classList.remove('hidden');
        this.scrollToBottom();
    }
    
    hideTyping() {
        this.isTyping = false;
        this.typingIndicator.classList.add('hidden');
    }
    
    scrollToBottom() {
        setTimeout(() => {
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }, 100);
    }
    
    clearChat() {
        if (confirm('Deseja limpar toda a conversa?')) {
            this.messagesContainer.innerHTML = this.getWelcomeMessage();
            this.extractedData = null;
            this.conversationHistory = [];
            this.currentFile = null;
            this.saveChatHistory();
        }
    }
    
    getWelcomeMessage() {
        return `
            <div class="message-bot rounded-2xl p-4 max-w-md animate-fade-in">
                <div class="flex items-start">
                    <div class="w-8 h-8 bg-gradient-to-r from-primary to-secondary rounded-full flex items-center justify-center flex-shrink-0">
                        <i class="fas fa-robot text-sm"></i>
                    </div>
                    <div class="ml-3">
                        <div class="text-sm text-gray-400 mb-1">Assistente PIX</div>
                        <div class="text-gray-100">
                            👋 Olá! Sou seu assistente especializado em comprovantes PIX. 
                            <br><br>
                            Posso ajudar você a:
                            <ul class="mt-2 space-y-1 text-sm">
                                <li>📄 Extrair dados de comprovantes</li>
                                <li>💰 Analisar valores e destinatários</li>
                                <li>🔍 Responder perguntas sobre transações</li>
                                <li>📊 Gerar relatórios estruturados</li>
                            </ul>
                            <br>
                            <strong>Envie um comprovante ou faça uma pergunta!</strong>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    async checkAPIHealth() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/health`);
            const data = await response.json();
            
            if (data.status === 'online') {
                this.updateAPIStatus('online');
            } else {
                this.updateAPIStatus('offline');
            }
        } catch (error) {
            console.warn('API não disponível:', error);
            this.updateAPIStatus('offline');
        }
    }
    
    updateAPIStatus(status) {
        const statusElement = document.querySelector('.text-green-400, .text-red-400');
        if (!statusElement) return;
        
        if (status === 'online') {
            statusElement.innerHTML = `<i class="fas fa-circle text-xs mr-1 animate-pulse"></i>Online`;
            statusElement.className = 'text-green-400';
        } else {
            statusElement.innerHTML = `<i class="fas fa-circle text-xs mr-1"></i>Offline`;
            statusElement.className = 'text-red-400';
        }
    }
    
    saveChatHistory() {
        try {
            localStorage.setItem('pixtext_chat_history', JSON.stringify(this.conversationHistory));
        } catch (error) {
            console.warn('Erro ao salvar histórico:', error);
        }
    }
    
    loadChatHistory() {
        try {
            const saved = localStorage.getItem('pixtext_chat_history');
            if (saved) {
                this.conversationHistory = JSON.parse(saved);
                // Não recarregar mensagens automaticamente para evitar spam
                console.log(`Histórico carregado: ${this.conversationHistory.length} mensagens`);
            }
        } catch (error) {
            console.warn('Erro ao carregar histórico:', error);
            this.conversationHistory = [];
        }
    }
    
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Inicializar chatbot quando DOM estiver carregado
let chatbot;
document.addEventListener('DOMContentLoaded', () => {
    chatbot = new PIXChatbot();
});

// Expor chatbot globalmente para uso nos botões
window.chatbot = chatbot;
