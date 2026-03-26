const API_BASE = "http://localhost:8000/api";
let currentChatId = null;
let currentLanguage = "en-US";

// --- Initializing UI ---
document.addEventListener('DOMContentLoaded', () => {
    loadChatList();

    // Auto-resize textarea
    const userInput = document.getElementById('user-input');
    userInput.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });

    // Use Enter to send message
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    document.getElementById('send-btn').addEventListener('click', sendMessage);

    // Toggle sidebar for small screens
    document.getElementById('toggle-sidebar').addEventListener('click', () => {
        const sidebar = document.getElementById('sidebar');
        sidebar.style.display = sidebar.style.display === 'none' ? 'flex' : 'none';
    });

    // Configure marked
    if (typeof markedKatex !== 'undefined') {
        marked.use(markedKatex({ throwOnError: false }));
    }

    marked.setOptions({
        highlight: function (code, lang) {
            if (lang && hljs.getLanguage(lang)) {
                return hljs.highlight(code, { language: lang }).value;
            }
            return hljs.highlightAuto(code).value;
        },
        breaks: true
    });
});

async function loadChatList() {
    try {
        const res = await fetch(`${API_BASE}/chats`);
        const chats = await res.json();
        const list = document.getElementById('chat-list');
        list.innerHTML = '';

        chats.forEach(chat => {
            const item = document.createElement('div');
            item.className = 'chat-item';
            if (chat.id === currentChatId) item.classList.add('active');

            const escapedTitle = chat.title.replace(/'/g, "\\'").replace(/"/g, '&quot;');
            item.innerHTML = `
                <div class="chat-title-wrap" title="${escapedTitle}" onclick="loadChat('${chat.id}', '${escapedTitle}')">
                    <i class="far fa-comment-dots"></i> <span>${chat.title}</span>
                </div>
                <div class="chat-actions-btn">
                    <button title="Rename" onclick="renameChat(event, '${chat.id}', '${escapedTitle}')"><i class="fas fa-edit"></i></button>
                    <button title="Delete" onclick="deleteChat(event, '${chat.id}')"><i class="fas fa-trash"></i></button>
                </div>
            `;
            list.appendChild(item);
        });
    } catch (err) {
        console.error("Failed to load chats:", err);
    }
}

async function createNewChat(titleOpt = null) {
    const title = titleOpt || prompt("Chat title:", "New Study");
    if (!title) return null;

    const formData = new FormData();
    formData.append('title', title);

    try {
        const res = await fetch(`${API_BASE}/chats`, {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        currentChatId = data.chat_id;
        
        // Immediate activation: update UI before returning
        document.getElementById('current-chat-title').innerText = data.title;
        document.getElementById('chat-messages').innerHTML = ''; 
        
        loadChatList(); 
        return currentChatId;
    } catch (err) {
        console.error("Failed to create chat:", err);
        return null;
    }
}

async function loadChat(chatId, title) {
    currentChatId = chatId;
    document.getElementById('current-chat-title').innerText = title;

    // Update active state in sidebar
    document.querySelectorAll('.chat-item').forEach(el => {
        el.classList.remove('active');
        if (el.innerText.trim() === title) el.classList.add('active');
    });

    const messagesPane = document.getElementById('chat-messages');
    messagesPane.innerHTML = '<div class="loader">Loading messages...</div>';

    try {
        const res = await fetch(`${API_BASE}/chats/${chatId}/messages`);
        const messages = await res.json();
        messagesPane.innerHTML = '';

        if (messages.length === 0) {
            const titleMsg = currentLanguage === 'pt-PT' ? 'Chat iniciado' : 'Chat started';
            const subMsg = currentLanguage === 'pt-PT' ? 'Estou pronto para as tuas dúvidas.' : 'I am ready for your questions.';
            messagesPane.innerHTML = `<div class="welcome-screen"><h2>${titleMsg}: ${title}</h2><p>${subMsg}</p></div>`;
        } else {
            messages.forEach(msg => appendMessage(msg.role, msg.content));
        }
        renderMathInPane(messagesPane);
        renderCircuits(messagesPane);
    } catch (err) {
        console.error("Failed to load messages:", err);
        messagesPane.innerHTML = 'Error loading messages.';
    }
}

function renderMathInPane(element) {
    if (typeof renderMathInElement !== 'undefined') {
        renderMathInElement(element, {
            delimiters: [
                { left: "$$", right: "$$", display: true },
                { left: "$", right: "$", display: false },
                { left: "\\(", right: "\\)", display: false },
                { left: "\\[", right: "\\]", display: true },
                { left: "\\begin{equation}", right: "\\end{equation}", display: true },
                { left: "\\begin{align}", right: "\\end{align}", display: true },
                { left: "\\begin{gather}", right: "\\end{gather}", display: true },
                { left: "\\begin{CD}", right: "\\end{CD}", display: true }
            ],
            throwOnError: false
        });
    }
}

function renderCircuits(element) {
    // Look for Tikz code blocks in the element
    const codeBlocks = element.querySelectorAll('code.language-latex, code.language-tex');
    codeBlocks.forEach(block => {
        const content = block.innerText;
        if (content.includes('\\begin{circuitikz}') || content.includes('\\begin{tikzpicture}')) {
            const tikzScript = document.createElement('script');
            tikzScript.type = 'text/tikz';
            tikzScript.textContent = content;
            block.parentElement.replaceWith(tikzScript);
        }
    });

    // Re-trigger TikzJax if it's already loaded
    if (window.Litz) {
        // TikzJax handles global scripts automatically, but for dynamic content
        // we might need to trigger a re-run if TikzJax supports it.
        // Actually TikzJax (v1) observes DOM changes if configured, 
        // or we can just let it find the new scripts.
    }
}

function appendMessage(role, content) {
    const pane = document.getElementById('chat-messages');
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}`;

    if (role === 'assistant') {
        const header = `<div class="ai-header"><i class="fas fa-robot"></i> ACIsstant</div>`;
        const bodyClass = `class="ai-body"`;

        if (content === 'TYPING') {
            msgDiv.innerHTML = `${header}<div ${bodyClass}><div class="typing-indicator"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div></div>`;
        } else {
            msgDiv.innerHTML = `${header}<div ${bodyClass}>${marked.parse(content)}</div>`;
        }
    } else {
        msgDiv.innerText = content;
    }

    pane.appendChild(msgDiv);

    // Smooth scroll to bottom
    setTimeout(() => {
        pane.scrollTo({ top: pane.scrollHeight, behavior: 'smooth' });
    }, 10);

    return msgDiv;
}

async function sendMessage() {
    const input = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const message = input.value.trim();
    if (!message) return;

    if (!currentChatId) {
        const newId = await createNewChat("Auto Chat");
        if (!newId) return;
    }

    input.value = '';
    input.style.height = 'auto';
    sendBtn.disabled = true;

    // Add user message to UI
    appendMessage('user', message);

    // Add assistant message placeholder as typing indicator
    const assistantMsgDiv = appendMessage('assistant', 'TYPING');
    let fullContent = "";

    try {
        const response = await fetch(`${API_BASE}/chat/stream`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                chat_id: currentChatId,
                message: message,
                language: currentLanguage
            })
        });

        if (!response.ok) throw new Error("Server response error");

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let isFirstChunk = true;
        let chunkCount = 0;
        const chatIdAtStart = currentChatId;

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            // Stop updating UI if user switched chats
            if (currentChatId !== chatIdAtStart) {
                // We let the loop finish to capture fullContent for the DB
                const chunk = decoder.decode(value, { stream: true });
                fullContent += chunk;
                continue;
            }

            const chunk = decoder.decode(value, { stream: true });
            fullContent += chunk;
            chunkCount++;

            if (isFirstChunk) {
                assistantMsgDiv.querySelector('.ai-body').innerHTML = '';
                isFirstChunk = false;
            }

            const pane = document.getElementById('chat-messages');
            const isScrolledToBottom = pane.scrollHeight - pane.clientHeight <= pane.scrollTop + 80;

            const bodyEl = assistantMsgDiv.querySelector('.ai-body');
            
            let displayContent = fullContent;
            let sourcesFound = "";
            if (fullContent.includes("\n\nSOURCES: ")) {
                const parts = fullContent.split("\n\nSOURCES: ");
                displayContent = parts[0];
                sourcesFound = parts[1];
            }

            bodyEl.innerHTML = marked.parse(displayContent);
            
            if (sourcesFound) {
                let sourcesBox = assistantMsgDiv.querySelector('.sources-box');
                if (!sourcesBox) {
                    sourcesBox = document.createElement('div');
                    sourcesBox.className = 'sources-box';
                    assistantMsgDiv.appendChild(sourcesBox);
                }
                const label = currentLanguage === 'pt-PT' ? 'Fontes Utilizadas' : 'Sources Used';
                sourcesBox.innerHTML = `<strong><i class="fas fa-book"></i> ${label}:</strong><br>${sourcesFound}`;
            }

            // Optimization: Only render math/circuits every 8 chunks to keep UI responsive
            if (chunkCount % 8 === 0) {
                renderMathInPane(bodyEl);
                renderCircuits(bodyEl);
            }

            if (isScrolledToBottom) {
                pane.scrollTop = pane.scrollHeight;
            }
        }
        
        // Final render to ensure everything is perfect
        if (currentChatId === chatIdAtStart) {
            const bodyEl = assistantMsgDiv.querySelector('.ai-body');
            renderMathInPane(bodyEl);
            renderCircuits(bodyEl);
        }
    } catch (err) {
        console.error("Streaming error:", err);
        assistantMsgDiv.querySelector('.ai-body').innerHTML = `<span style="color:#ef4444;"><i class="fas fa-exclamation-triangle"></i> Communication error with server. Check if the backend is running.</span>`;
    } finally {
        sendBtn.disabled = false;
        input.focus();
    }
}

function updateLanguage() {
    currentLanguage = document.getElementById('lang-select').value;
    
    // UI Elements translation map
    const translations = {
        'en-US': {
            'btn-new-chat': '<i class="fas fa-plus"></i> New Chat',
            'btn-upload': '<i class="fas fa-file-upload"></i> Upload & Index RAG',
            'btn-files': '<i class="fas fa-folder-open"></i> Files',
            'model-status': 'Model Ready (Qwen 3B)',
            'current-chat-title': currentChatId ? document.getElementById('current-chat-title').innerText : 'Welcome',
            'welcome-title': 'Hello!',
            'welcome-subtitle': 'How can I help you with your Electronics and Signals studies today?',
            'footer-note': 'Qwen2.5 3B | Local Offline Inference',
            'user-input-placeholder': 'Type your question here...',
            'modal-title': '<i class="fas fa-folder-open"></i> Uploaded Documents',
            'suggestions': [
                { text: 'Low-Pass Filters', query: 'Explain a 2nd order low-pass filter' },
                { text: 'Op-Amps', query: 'Explain the operating principle of an Op-Amp' },
                { text: 'LaTeX Circuit', query: 'Generate a simple circuit in LaTeX (Circuitikz)' }
            ]
        },
        'pt-PT': {
            'btn-new-chat': '<i class="fas fa-plus"></i> Novo Chat',
            'btn-upload': '<i class="fas fa-file-upload"></i> Carregar e Indexar RAG',
            'btn-files': '<i class="fas fa-folder-open"></i> Ficheiros',
            'model-status': 'Modelo Pronto (Qwen 3B)',
            'current-chat-title': currentChatId ? document.getElementById('current-chat-title').innerText : 'Bem-vindo',
            'welcome-title': 'Olá!',
            'welcome-subtitle': 'Como posso ajudar nos teus estudos de Eletrónica e Sinais hoje?',
            'footer-note': 'Qwen2.5 3B | Inferência Local Offline',
            'user-input-placeholder': 'Escreve a tua pergunta aqui...',
            'modal-title': '<i class="fas fa-folder-open"></i> Documentos Carregados',
            'suggestions': [
                { text: 'Filtros Passa-Baixo', query: 'Explica um filtro passa-baixo de 2ª ordem' },
                { text: 'Amps-Op', query: 'Explica o princípio de funcionamento de um Amp-Op' },
                { text: 'Circuito LaTeX', query: 'Gera um circuito simples em LaTeX (Circuitikz)' }
            ]
        }
    };

    const t = translations[currentLanguage];

    // Apply translations
    document.getElementById('btn-new-chat').innerHTML = t['btn-new-chat'];
    document.getElementById('btn-upload').innerHTML = t['btn-upload'];
    document.getElementById('btn-files').innerHTML = t['btn-files'];
    document.getElementById('model-status').innerText = t['model-status'];
    if (!currentChatId) document.getElementById('current-chat-title').innerText = t['current-chat-title'];
    
    if (document.getElementById('welcome-screen')) {
        document.getElementById('welcome-title').innerText = t['welcome-title'];
        document.getElementById('welcome-subtitle').innerText = t['welcome-subtitle'];
        
        const suggs = document.getElementById('welcome-suggestions');
        suggs.innerHTML = '';
        t.suggestions.forEach(s => {
            const btn = document.createElement('button');
            btn.innerText = s.text;
            btn.onclick = () => quickAction(s.query);
            suggs.appendChild(btn);
        });
    }

    document.getElementById('user-input').placeholder = t['user-input-placeholder'];
    document.getElementById('footer-note').innerText = t['footer-note'];
    document.querySelector('.modal-header h3').innerHTML = t['modal-title'];
}

function quickAction(text) {
    document.getElementById('user-input').value = text;
    sendMessage(); // Auto-send when clicking suggestions
}

async function uploadFiles(files) {
    if (!files || files.length === 0) return;

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
        formData.append("files", files[i]);
    }

    const btn = document.querySelector('.fa-file-upload').parentElement;
    const oldHtml = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Indexing...';
    btn.disabled = true;

    try {
        const res = await fetch(`${API_BASE}/upload`, {
            method: 'POST',
            body: formData
        });
        const data = await res.json();

        if (res.ok) {
            alert(`Success! ${data.files.length} document(s) indexed in RAG.`);
        } else {
            alert(`Indexing error: ${data.detail || 'Unknown error'}`);
        }
    } catch (err) {
        console.error("Upload error:", err);
        alert("Network failure when uploading files.");
    } finally {
        btn.innerHTML = oldHtml;
        btn.disabled = false;
        // Reset file input
        document.getElementById('file-upload').value = '';
    }
}

async function renameChat(evt, chatId, currentTitle) {
    evt.stopPropagation();
    const newTitle = prompt("New name:", currentTitle);
    if (!newTitle || newTitle.trim() === "" || newTitle === currentTitle) return;

    const formData = new FormData();
    formData.append('title', newTitle.trim());

    try {
        const res = await fetch(`${API_BASE}/chats/${chatId}`, {
            method: 'PUT',
            body: formData
        });
        if (res.ok) {
            if (currentChatId === chatId) {
                document.getElementById('current-chat-title').innerText = newTitle.trim();
            }
            loadChatList();
        }
    } catch (err) {
        console.error("Failed to rename chat:", err);
    }
}

async function deleteChat(evt, chatId) {
    evt.stopPropagation();
    if (!confirm("Are you sure you want to delete this chat?")) return;

    try {
        const res = await fetch(`${API_BASE}/chats/${chatId}`, {
            method: 'DELETE'
        });
        if (res.ok) {
            if (currentChatId === chatId) {
                currentChatId = null;
                document.getElementById('chat-messages').innerHTML = `<div class="welcome-screen"><h2>Chat Deleted</h2><p>Start a new conversation.</p></div>`;
                document.getElementById('current-chat-title').innerText = 'Welcome';
            }
            loadChatList();
        }
    } catch (err) {
        console.error("Failed to delete chat:", err);
    }
}

function showSettings() {
    // Simple hardware info for now
    alert("ACIsstant Hardware Settings:\n\nMode: Auto-Optimize\nCPU Threads: Automatic (Detected Cores - 1)\nContext Window: Scaling by RAM (4k-32k)\n\nTo change manual settings, edit 'backend/llm.py'. UI control coming soon in V2!");
}

/* --- Files Management Logic --- */
let allFiles = [];

async function toggleFilesModal() {
    const modal = document.getElementById('files-modal');
    if (modal.style.display === 'none') {
        modal.style.display = 'flex';
        await loadUploadedFiles();
    } else {
        modal.style.display = 'none';
    }
}

async function loadUploadedFiles() {
    const grid = document.getElementById('files-grid');
    grid.innerHTML = '<div class="loader">Loading files...</div>';
    
    try {
        const res = await fetch(`${API_BASE.replace('/api', '')}/api/files`);
        allFiles = await res.json();
        renderFiles(allFiles);
    } catch (err) {
        console.error("Failed to load files:", err);
        grid.innerHTML = '<div class="error">Error loading files.</div>';
    }
}

function renderFiles(files) {
    const grid = document.getElementById('files-grid');
    grid.innerHTML = '';
    
    if (files.length === 0) {
        grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; color: #94a3b8; padding: 40px;">No files found.</div>';
        return;
    }
    
    files.forEach(file => {
        const card = document.createElement('div');
        card.className = 'file-card';
        
        let iconClass = 'fa-file-alt';
        if (file.extension === 'pdf') iconClass = 'fa-file-pdf';
        if (file.extension === 'md') iconClass = 'fa-file-code';
        if (['jpg', 'png', 'svg'].includes(file.extension)) iconClass = 'fa-file-image';
        
        card.innerHTML = `
            <i class="fas ${iconClass} file-icon"></i>
            <div class="file-name" title="${file.name}">${file.name}</div>
            <div class="file-actions">
                <button class="file-btn btn-open" onclick="openFile('${file.path}')">
                    <i class="fas fa-external-link-alt"></i> Open
                </button>
            </div>
        `;
        grid.appendChild(card);
    });
}

function filterFiles(ext, btn) {
    // Update active state of buttons
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    
    if (ext === 'all') {
        renderFiles(allFiles);
    } else {
        const filtered = allFiles.filter(f => f.extension === ext);
        renderFiles(filtered);
    }
}

function openFile(path) {
    const url = `${API_BASE.replace('/api', '')}/api/files/download/${path}`;
    window.open(url, '_blank');
}

// Global Hotkeys
window.addEventListener('keydown', async (e) => {
    // Ctrl+R to Restart AI
    if (e.ctrlKey && (e.key === 'r' || e.key === 'R')) {
        e.preventDefault();
        console.log("ACIsstant: Hot-Restart Triggered (Ctrl+R)");
        try {
            await fetch(`${API_BASE.replace('/api', '')}/api/restart`, { method: 'POST' });
            // Show a small overlay or just wait for the server to die
            document.body.innerHTML = `
                <div style="background:#000; color:#a855f7; height:100vh; display:flex; align-items:center; justify-content:center; font-family:sans-serif; flex-direction:column; gap:20px;">
                    <i class="fas fa-sync fa-spin" style="font-size:3rem;"></i>
                    <h1>Restarting ACIsstant...</h1>
                    <p>The server is rebooting. This page will refresh automatically.</p>
                </div>
            `;
            setTimeout(() => location.reload(), 5000);
        } catch (err) {
            console.error("Restart failed", err);
        }
    }
});
