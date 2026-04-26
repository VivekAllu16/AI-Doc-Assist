document.addEventListener('DOMContentLoaded', () => {
    const uploadBox = document.getElementById('uploadBox');
    const fileInput = document.getElementById('fileInput');
    const uploadStatus = document.getElementById('uploadStatus');
    const fileInfo = document.getElementById('fileInfo');
    const fileNameDisplay = document.getElementById('fileName');
    
    const chatHistory = document.getElementById('chatHistory');
    const chatForm = document.getElementById('chatForm');
    const questionInput = document.getElementById('questionInput');
    const sendBtn = document.getElementById('sendBtn');
    
    const systemStatusDot = document.getElementById('systemStatusDot');
    const systemStatusText = document.getElementById('systemStatusText');
    
    let isDocumentReady = false;

    // --- File Upload Logic ---
    
    // Click to upload
    uploadBox.addEventListener('click', () => {
        if (!isDocumentReady) fileInput.click();
    });

    // Drag and drop
    uploadBox.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadBox.classList.add('dragover');
    });

    uploadBox.addEventListener('dragleave', () => {
        uploadBox.classList.remove('dragover');
    });

    uploadBox.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadBox.classList.remove('dragover');
        
        if (e.dataTransfer.files.length > 0) {
            handleFile(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });

    async function handleFile(file) {
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            alert('Please upload a PDF file.');
            return;
        }

        // Show loading state
        uploadBox.classList.add('hidden');
        uploadStatus.classList.remove('hidden');
        
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                // Success state
                uploadStatus.classList.add('hidden');
                fileInfo.classList.remove('hidden');
                fileNameDisplay.textContent = file.name;
                
                isDocumentReady = true;
                questionInput.disabled = false;
                sendBtn.disabled = false;
                
                systemStatusDot.classList.remove('offline');
                systemStatusDot.classList.add('online');
                systemStatusText.textContent = 'Document Ready';
                
                addMessage('bot', `I've successfully analyzed "${file.name}". What would you like to know about it?`);
            } else {
                throw new Error(result.detail || 'Failed to process document');
            }
        } catch (error) {
            alert(error.message);
            // Reset state
            uploadStatus.classList.add('hidden');
            uploadBox.classList.remove('hidden');
            fileInput.value = '';
        }
    }

    // --- Chat Logic ---

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const question = questionInput.value.trim();
        if (!question || !isDocumentReady) return;
        
        // Add user message
        addMessage('user', question);
        questionInput.value = '';
        questionInput.disabled = true;
        sendBtn.disabled = true;
        
        // Add typing indicator
        const typingId = addTypingIndicator();
        
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ question })
            });
            
            const result = await response.json();
            
            // Remove typing indicator
            document.getElementById(typingId).remove();
            
            if (response.ok) {
                addMessage('bot', result.answer);
            } else {
                addMessage('system', `Error: ${result.detail || 'Failed to get answer'}`);
            }
        } catch (error) {
            document.getElementById(typingId).remove();
            addMessage('system', 'Sorry, there was a network error. Please try again.');
        } finally {
            questionInput.disabled = false;
            sendBtn.disabled = false;
            questionInput.focus();
        }
    });

    function addMessage(sender, text) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender}-message`;
        
        let iconClass = 'fa-robot';
        if (sender === 'user') iconClass = 'fa-user';
        if (sender === 'system') iconClass = 'fa-triangle-exclamation';

        msgDiv.innerHTML = `
            <div class="avatar"><i class="fa-solid ${iconClass}"></i></div>
            <div class="message-content">${escapeHTML(text)}</div>
        `;
        
        chatHistory.appendChild(msgDiv);
        scrollToBottom();
    }
    
    function addTypingIndicator() {
        const id = 'typing-' + Date.now();
        const msgDiv = document.createElement('div');
        msgDiv.className = `message bot-message`;
        msgDiv.id = id;
        
        msgDiv.innerHTML = `
            <div class="avatar"><i class="fa-solid fa-robot"></i></div>
            <div class="message-content">
                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;
        
        chatHistory.appendChild(msgDiv);
        scrollToBottom();
        return id;
    }

    function scrollToBottom() {
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    function escapeHTML(str) {
        return str.replace(/[&<>'"]/g, 
            tag => ({
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                "'": '&#39;',
                '"': '&quot;'
            }[tag] || tag)
        );
    }
});
