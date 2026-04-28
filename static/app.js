document.addEventListener('DOMContentLoaded', () => {
    // Auth Elements
    const authScreen = document.getElementById('authScreen');
    const mainApp = document.getElementById('mainApp');
    const tabLogin = document.getElementById('tabLogin');
    const tabRegister = document.getElementById('tabRegister');
    const authForm = document.getElementById('authForm');
    const authBtn = document.getElementById('authBtn');
    const authError = document.getElementById('authError');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const displayUsername = document.getElementById('displayUsername');
    const logoutBtn = document.getElementById('logoutBtn');
    
    // App Elements
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
    
    let isLoginMode = true;
    let authToken = localStorage.getItem('authToken');
    let hasDocuments = false;

    // --- Authentication Logic ---
    
    function switchMode(isLogin) {
        isLoginMode = isLogin;
        tabLogin.classList.toggle('active', isLogin);
        tabRegister.classList.toggle('active', !isLogin);
        authBtn.textContent = isLogin ? 'Sign In' : 'Register';
        authError.classList.add('hidden');
    }

    tabLogin.addEventListener('click', () => switchMode(true));
    tabRegister.addEventListener('click', () => switchMode(false));

    authForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        authBtn.disabled = true;
        authError.classList.add('hidden');
        
        const username = usernameInput.value;
        const password = passwordInput.value;
        
        try {
            let response;
            if (isLoginMode) {
                // Login uses form data
                const formData = new URLSearchParams();
                formData.append('username', username);
                formData.append('password', password);
                
                response = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: formData
                });
            } else {
                // Register uses JSON
                response = await fetch('/api/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });
            }
            
            const result = await response.json();
            
            if (response.ok) {
                authToken = result.access_token;
                localStorage.setItem('authToken', authToken);
                displayUsername.textContent = result.username;
                showMainApp();
            } else {
                authError.textContent = result.detail || 'Authentication failed';
                authError.classList.remove('hidden');
            }
        } catch (error) {
            authError.textContent = 'Network error. Please try again.';
            authError.classList.remove('hidden');
        } finally {
            authBtn.disabled = false;
        }
    });

    logoutBtn.addEventListener('click', () => {
        localStorage.removeItem('authToken');
        authToken = null;
        hasDocuments = false;
        chatHistory.innerHTML = '';
        authScreen.classList.remove('hidden');
        mainApp.classList.add('hidden');
        resetUploadState();
    });

    async function showMainApp() {
        authScreen.classList.add('hidden');
        mainApp.classList.remove('hidden');
        await loadChatHistory();
    }

    async function loadChatHistory() {
        try {
            const response = await fetch('/api/history', {
                headers: { 'Authorization': `Bearer ${authToken}` }
            });
            if (response.ok) {
                const history = await response.json();
                chatHistory.innerHTML = ''; // Clear history
                
                if (history.length === 0) {
                    addMessage('system', "Hello! I'm your AI Document Assistant. Please upload PDF documents on the left to begin.");
                } else {
                    history.forEach(msg => {
                        addMessage(msg.sender, msg.message, false); // false to not scroll on every message
                    });
                    scrollToBottom();
                }
            } else if (response.status === 401) {
                logoutBtn.click(); // Token expired
            }
        } catch (error) {
            console.error('Failed to load history', error);
        }
    }

    // Check auth on load
    if (authToken) {
        // Assume valid, we could ping a /me endpoint but let's just fetch history to verify
        // The loadChatHistory will log us out if it returns 401
        displayUsername.textContent = "Welcome back";
        showMainApp();
    }

    // --- File Upload Logic ---
    
    uploadBox.addEventListener('click', () => {
        if (!hasDocuments) fileInput.click();
    });

    uploadBox.addEventListener('dragover', (e) => { e.preventDefault(); uploadBox.classList.add('dragover'); });
    uploadBox.addEventListener('dragleave', () => { uploadBox.classList.remove('dragover'); });

    uploadBox.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadBox.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleFiles(e.dataTransfer.files);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFiles(e.target.files);
        }
    });

    async function handleFiles(files) {
        const formData = new FormData();
        let validFilesCount = 0;
        
        for (let i = 0; i < files.length; i++) {
            if (files[i].name.toLowerCase().endsWith('.pdf')) {
                formData.append('files', files[i]);
                validFilesCount++;
            }
        }
        
        if (validFilesCount === 0) {
            alert('Please upload valid PDF files.');
            return;
        }

        uploadBox.classList.add('hidden');
        uploadStatus.classList.remove('hidden');
        
        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${authToken}` },
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                uploadStatus.classList.add('hidden');
                fileInfo.classList.remove('hidden');
                fileNameDisplay.textContent = `${validFilesCount} document(s) loaded`;
                
                hasDocuments = true;
                questionInput.disabled = false;
                sendBtn.disabled = false;
                
                systemStatusDot.classList.remove('offline');
                systemStatusDot.classList.add('online');
                systemStatusText.textContent = 'Documents Ready';
                
                addMessage('bot', `I've successfully analyzed your documents. What would you like to know about them?`);
            } else {
                throw new Error(result.detail || 'Failed to process documents');
            }
        } catch (error) {
            alert(error.message);
            resetUploadState();
        }
    }

    function resetUploadState() {
        uploadStatus.classList.add('hidden');
        fileInfo.classList.add('hidden');
        uploadBox.classList.remove('hidden');
        fileInput.value = '';
        systemStatusDot.classList.add('offline');
        systemStatusDot.classList.remove('online');
        systemStatusText.textContent = 'Awaiting Documents';
    }

    // --- Chat Logic ---

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const question = questionInput.value.trim();
        if (!question || !hasDocuments) return;
        
        addMessage('user', question);
        questionInput.value = '';
        questionInput.disabled = true;
        sendBtn.disabled = true;
        
        const typingId = addTypingIndicator();
        
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authToken}`
                },
                body: JSON.stringify({ question })
            });
            
            const result = await response.json();
            document.getElementById(typingId).remove();
            
            if (response.ok) {
                addMessage('bot', result.answer);
            } else if (response.status === 401) {
                logoutBtn.click();
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

    function addMessage(sender, text, doScroll = true) {
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
        if (doScroll) scrollToBottom();
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

    function scrollToBottom() { chatHistory.scrollTop = chatHistory.scrollHeight; }

    function escapeHTML(str) {
        return str.replace(/[&<>'"]/g, 
            tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
        );
    }
});
