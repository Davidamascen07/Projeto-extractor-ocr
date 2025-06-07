class PIXExtractorApp {
    constructor() {
        this.apiBaseUrl = 'http://localhost:5000/api';
        this.currentFile = null;
        this.extractionResult = null;
        
        this.init();
    }
    
    init() {
        this.setupElements();
        this.setupEventListeners();
        this.checkAPIHealth();
    }
    
    setupElements() {
        // Upload elements
        this.dropArea = document.getElementById('drop-area');
        this.fileInput = document.getElementById('file-input');
        this.uploadBtn = document.getElementById('upload-btn');
        this.filePreview = document.getElementById('file-preview');
        this.previewImage = document.getElementById('preview-image');
        this.pdfPreview = document.getElementById('pdf-preview');
        this.pdfName = document.getElementById('pdf-name');
        this.removeFile = document.getElementById('remove-file');
        this.extractBtn = document.getElementById('extract-btn');
        
        // Progress elements
        this.progressContainer = document.getElementById('progress-container');
        this.progressPercent = document.getElementById('progress-percent');
        this.progressBar = document.querySelector('.progress-bar');
        
        // Result elements
        this.resultEmpty = document.getElementById('result-empty');
        this.resultContent = document.getElementById('result-content');
        this.apiStatus = document.getElementById('api-status');
    }
    
    setupEventListeners() {
        // Upload events
        this.uploadBtn.addEventListener('click', () => this.fileInput.click());
        this.fileInput.addEventListener('change', (e) => this.handleFileSelection(e));
        this.removeFile.addEventListener('click', () => this.clearFile());
        this.extractBtn.addEventListener('click', () => this.extractData());
        
        // Drag and drop
        this.setupDragAndDrop();
        
        // Demo button - corrigido para procurar pelo seletor correto
        const demoBtn = document.querySelector('button:has(i.fa-play-circle)') || 
                        document.querySelector('.group') ||
                        document.querySelector('button[class*="group"]');
        if (demoBtn) {
            demoBtn.addEventListener('click', () => this.showDemo());
        }
        
        // Botões de ação nos resultados
        const downloadBtn = document.getElementById('download-btn');
        const extractAnotherBtn = document.getElementById('extract-another-btn');
        
        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => this.downloadResults());
        }
        
        if (extractAnotherBtn) {
            extractAnotherBtn.addEventListener('click', () => this.clearFile());
        }
        
        // Navegação - adicionar links para chatbot
        this.setupNavigation();
    }
    
    setupNavigation() {
        // Adicionar link para chatbot no header
        const nav = document.querySelector('nav');
        if (nav) {
            const chatbotLink = document.createElement('a');
            chatbotLink.href = 'chatbot.html';
            chatbotLink.className = 'px-4 py-2 rounded-lg hover:bg-gray-800 transition';
            chatbotLink.innerHTML = '<i class="fas fa-robot mr-2"></i>Chatbot';
            nav.appendChild(chatbotLink);
        }
    }
    
    downloadResults() {
        if (!this.extractionResult) {
            this.showError('Nenhum resultado para download');
            return;
        }
        
        // Criar conteúdo do arquivo
        const content = this.generateDownloadContent(this.extractionResult);
        
        // Criar e fazer download do arquivo
        const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `pix_extraction_${new Date().toISOString().slice(0, 10)}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        // Mostrar feedback
        this.showSuccess('Arquivo baixado com sucesso!');
    }
    
    generateDownloadContent(data) {
        const timestamp = new Date().toLocaleString('pt-BR');
        
        return `PIXText.ai - Extração de Comprovante PIX
Processado em: ${timestamp}

====== DADOS EXTRAÍDOS ======

Valor: ${this.formatCurrency(data.valor_total || data.valor_numerico || 0)}
Destinatário: ${data.destino_nome || data.recebedor_nome || 'Não identificado'}
CPF: ${data.destino_cpf || data.recebedor_cpf || 'Não identificado'}
Remetente: ${data.origem_nome || data.pagador_nome || 'Não identificado'}
Data: ${data.data_hora || data.data || 'Não identificada'}
ID da Transação: ${data.codigo_operacao || data.id_transacao || 'Não identificado'}

====== TEXTO COMPLETO ======

${data.raw_text || data.cleaned_text || 'Texto não disponível'}

====== INFORMAÇÕES TÉCNICAS ======

Layout Detectado: ${data.layout_detectado || 'Genérico'}
Modo de Processamento: ${data.mode || 'N/A'}
Arquivo Original: ${this.currentFile ? this.currentFile.name : 'N/A'}

---
Gerado por PIXText.ai - Sistema de Extração OCR
`;
    }
    
    showSuccess(message) {
        // Criar elemento de sucesso
        let successElement = document.getElementById('success-message');
        if (!successElement) {
            successElement = document.createElement('div');
            successElement.id = 'success-message';
            successElement.className = 'fixed top-4 right-4 bg-green-600 text-white px-6 py-3 rounded-lg shadow-lg z-50';
            document.body.appendChild(successElement);
        }
        
        successElement.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-check-circle mr-2"></i>
                <span>${message}</span>
                <button class="ml-4 text-white hover:text-gray-200" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        // Auto remover após 3 segundos
        setTimeout(() => {
            if (successElement.parentElement) {
                successElement.remove();
            }
        }, 3000);
    }
    
    async extractData() {
        if (!this.currentFile) return;
        
        this.showProgress();
        
        const formData = new FormData();
        formData.append('file', this.currentFile);
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/extract`, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                this.extractionResult = result.data;
                this.showResults(result.data);
            } else {
                throw new Error(result.error || 'Erro na extração');
            }
            
        } catch (error) {
            console.error('Erro na extração:', error);
            this.showError(`Erro ao processar arquivo: ${error.message}`);
        } finally {
            this.hideProgress();
        }
    }
    
    showProgress() {
        this.progressContainer.classList.remove('hidden');
        this.extractBtn.disabled = true;
        
        let progress = 0;
        const interval = setInterval(() => {
            progress += 5;
            this.progressBar.style.width = progress + '%';
            this.progressPercent.textContent = progress + '%';
            
            if (progress >= 95) {
                clearInterval(interval);
            }
        }, 100);
        
        // Armazenar intervalo para limpar depois
        this.progressInterval = interval;
    }
    
    hideProgress() {
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
        }
        
        // Completar progresso
        this.progressBar.style.width = '100%';
        this.progressPercent.textContent = '100%';
        
        setTimeout(() => {
            this.progressContainer.classList.add('hidden');
            this.extractBtn.disabled = false;
        }, 500);
    }
    
    showResults(data) {
        this.resultEmpty.classList.add('hidden');
        this.resultContent.classList.remove('hidden');
        
        // Atualizar dados na interface
        this.updateResultsDisplay(data);
    }
    
    updateResultsDisplay(data) {
        // Atualizar valores principais
        const valorElement = this.resultContent.querySelector('[data-field="valor"]');
        if (valorElement) {
            valorElement.textContent = this.formatCurrency(data.valor_total || data.valor_numerico || 0);
        }
        
        // Atualizar destinatário
        const destinatarioElement = this.resultContent.querySelector('[data-field="destinatario"]');
        if (destinatarioElement) {
            destinatarioElement.textContent = data.destino_nome || data.recebedor_nome || 'Não identificado';
        }
        
        // Atualizar CPF
        const cpfElement = this.resultContent.querySelector('[data-field="cpf"]');
        if (cpfElement) {
            cpfElement.textContent = data.destino_cpf || data.recebedor_cpf || 'Não identificado';
        }
        
        // Atualizar origem
        const origemElement = this.resultContent.querySelector('[data-field="origem"]');
        if (origemElement) {
            origemElement.textContent = data.origem_nome || data.pagador_nome || 'Não identificado';
        }
        
        // Atualizar data
        const dataElement = this.resultContent.querySelector('[data-field="data"]');
        if (dataElement) {
            dataElement.textContent = data.data_hora || data.data || 'Não identificada';
        }
        
        // Atualizar ID da transação
        const idElement = this.resultContent.querySelector('[data-field="transacao"]');
        if (idElement) {
            idElement.textContent = data.codigo_operacao || data.id_transacao || 'Não identificado';
        }
        
        // Atualizar texto completo
        const textoElement = this.resultContent.querySelector('[data-field="texto-completo"]');
        if (textoElement) {
            textoElement.textContent = data.raw_text || data.cleaned_text || 'Texto não disponível';
        }
        
        // Atualizar badges de status
        this.updateStatusBadges(data);
    }
    
    updateStatusBadges(data) {
        const confianca = data.layout_detectado !== 'generico' ? 'Alta' : 'Média';
        const tempo = '1.8s'; // Simulado
        
        const badgeContainer = this.resultContent.querySelector('.flex.flex-wrap.gap-3');
        if (badgeContainer) {
            badgeContainer.innerHTML = `
                <span class="bg-indigo-900 text-primary px-3 py-1 rounded-lg text-sm">
                    <i class="fas fa-check-circle mr-1"></i> Confiança ${confianca}
                </span>
                <span class="bg-blue-900 text-secondary px-3 py-1 rounded-lg text-sm">
                    <i class="fas fa-bolt mr-1"></i> Processado em ${tempo}
                </span>
                <span class="bg-green-900 text-green-300 px-3 py-1 rounded-lg text-sm">
                    <i class="fas fa-brain mr-1"></i> ${data.layout_detectado || 'Genérico'}
                </span>
            `;
        }
    }
    
    hideResults() {
        this.resultEmpty.classList.remove('hidden');
        this.resultContent.classList.add('hidden');
    }
    
    formatCurrency(value) {
        if (typeof value !== 'number') return 'R$ 0,00';
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value);
    }
    
    showError(message) {
        // Criar ou atualizar elemento de erro
        let errorElement = document.getElementById('error-message');
        if (!errorElement) {
            errorElement = document.createElement('div');
            errorElement.id = 'error-message';
            errorElement.className = 'fixed top-4 right-4 bg-red-600 text-white px-6 py-3 rounded-lg shadow-lg z-50';
            document.body.appendChild(errorElement);
        }
        
        errorElement.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-exclamation-triangle mr-2"></i>
                <span>${message}</span>
                <button class="ml-4 text-white hover:text-gray-200" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        // Auto remover após 5 segundos
        setTimeout(() => {
            if (errorElement.parentElement) {
                errorElement.remove();
            }
        }, 5000);
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
        if (!this.apiStatus) return;
        
        if (status === 'online') {
            this.apiStatus.innerHTML = `
                <span class="text-green-400">
                    <i class="fas fa-circle text-xs mr-1 animate-pulse"></i>API Online
                </span>
            `;
        } else {
            this.apiStatus.innerHTML = `
                <span class="text-red-400">
                    <i class="fas fa-circle text-xs mr-1"></i>API Offline
                </span>
            `;
        }
    }
    
    showDemo() {
        // Mostrar dados de demonstração reais
        const demoData = {
            layout_detectado: 'nubank',
            valor_total: 2347.50,
            valor_numerico: 2347.50,
            destino_nome: 'Maria Silva Santos',
            destino_cpf: '123.456.789-00',
            origem_nome: 'João Carlos Oliveira',
            data_hora: '15/12/2023 14:35',
            codigo_operacao: 'PIX8H3F9K2L7M',
            raw_text: 'DEMONSTRAÇÃO - PIX Realizado\nValor: R$ 2.347,50\nPara: Maria Silva Santos\nCPF: 123.456.789-00\nData: 15/12/2023 14:35\nID: PIX8H3F9K2L7M\nNu Pagamentos S.A.',
            cleaned_text: 'Dados de demonstração do sistema PIXText.ai',
            mode: 'demo'
        };
        
        // Simular arquivo carregado
        this.currentFile = { name: 'demo_pix_comprovante.jpg', size: 1024000 };
        
        // Mostrar preview simulado
        this.previewImage.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iIzMzMzMzMyIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTYiIGZpbGw9IiNmZmZmZmYiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj5EZW1vbnN0cmHDp8OjbyBQSVg8L3RleHQ+PC9zdmc+';
        this.previewImage.classList.remove('hidden');
        this.pdfPreview.classList.add('hidden');
        this.filePreview.classList.remove('hidden');
        this.extractBtn.disabled = false;
        
        // Simular progresso
        this.showProgress();
        
        setTimeout(() => {
            this.hideProgress();
            this.extractionResult = demoData;
            this.showResults(demoData);
            this.showSuccess('Demonstração carregada com sucesso!');
        }, 2000);
        
        // Scroll para área de upload
        this.dropArea.scrollIntoView({ behavior: 'smooth' });
    }
    
    setupDragAndDrop() {
        if (!this.dropArea) return;
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            this.dropArea.addEventListener(eventName, this.preventDefaults, false);
            document.body.addEventListener(eventName, this.preventDefaults, false);
        });
        
        ['dragenter', 'dragover'].forEach(eventName => {
            this.dropArea.addEventListener(eventName, () => {
                this.dropArea.classList.add('drag-over');
            }, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            this.dropArea.addEventListener(eventName, () => {
                this.dropArea.classList.remove('drag-over');
            }, false);
        });
        
        this.dropArea.addEventListener('drop', (e) => this.handleDrop(e), false);
        
        // Adicionar click listener para a área de drop
        this.dropArea.addEventListener('click', () => {
            this.fileInput.click();
        });
    }
    
    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    handleDrop(e) {
        this.preventDefaults(e);
        const dt = e.dataTransfer;
        const files = dt.files;
        this.handleFiles(files);
    }
    
    handleFileSelection(e) {
        const files = e.target.files;
        this.handleFiles(files);
    }
    
    handleFiles(files) {
        if (files.length === 0) return;
        
        const file = files[0];
        
        console.log('Arquivo selecionado:', file.name, file.type, file.size);
        
        // Validar tipo de arquivo
        if (!this.isValidFileType(file)) {
            this.showError('Por favor, envie um arquivo de imagem (JPG, PNG) ou PDF.');
            return;
        }
        
        // Validar tamanho
        if (file.size > 16 * 1024 * 1024) { // 16MB
            this.showError('Arquivo muito grande. Tamanho máximo: 16MB');
            return;
        }
        
        this.currentFile = file;
        this.showFilePreview(file);
        this.extractBtn.disabled = false;
        
        console.log('Arquivo carregado com sucesso:', file.name);
    }
    
    isValidFileType(file) {
        const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf'];
        const isValid = allowedTypes.includes(file.type.toLowerCase());
        
        // Verificar também pela extensão do arquivo
        const fileName = file.name.toLowerCase();
        const allowedExtensions = ['.jpg', '.jpeg', '.png', '.pdf'];
        const hasValidExtension = allowedExtensions.some(ext => fileName.endsWith(ext));
        
        return isValid || hasValidExtension;
    }
    
    showFilePreview(file) {
        if (!this.filePreview) return;
        
        if (file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = (e) => {
                this.previewImage.src = e.target.result;
                this.previewImage.classList.remove('hidden');
                this.pdfPreview.classList.add('hidden');
                this.filePreview.classList.remove('hidden');
                console.log('Preview de imagem carregado');
            };
            reader.onerror = (e) => {
                console.error('Erro ao carregar preview:', e);
                this.showError('Erro ao carregar preview da imagem');
            };
            reader.readAsDataURL(file);
        } else if (file.type === 'application/pdf') {
            this.pdfName.textContent = file.name;
            this.pdfPreview.classList.remove('hidden');
            this.previewImage.classList.add('hidden');
            this.filePreview.classList.remove('hidden');
            console.log('Preview de PDF carregado');
        }
    }
    
    clearFile() {
        this.currentFile = null;
        this.fileInput.value = '';
        this.filePreview.classList.add('hidden');
        this.extractBtn.disabled = true;
        this.hideResults();
        console.log('Arquivo removido');
    }
}

// Inicializar aplicação quando DOM estiver carregado
document.addEventListener('DOMContentLoaded', () => {
    new PIXExtractorApp();
});
