const API_BASE = "http://localhost:8000/api";
let currentChatId = null;
let currentLanguage = "en-US";
let currentAbortController = null;

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
    document.getElementById('stop-btn').addEventListener('click', stopGenerating);

    // Toggle sidebar for small screens
    document.getElementById('toggle-sidebar').addEventListener('click', () => {
        const sidebar = document.getElementById('sidebar');
        sidebar.style.display = sidebar.style.display === 'none' ? 'flex' : 'none';
    });

    // Configure marked
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
        renderCircuits(messagesPane);
        startTokenPolling();
    } catch (err) {
        console.error("Failed to load messages:", err);
        messagesPane.innerHTML = 'Error loading messages.';
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
            // Reapply Math protection for history rendering (same as stream)
            let displayContent = content
                .replace(/\\\[/g, '$$$$')
                .replace(/\\\]/g, '$$$$')
                .replace(/\\\(/g, '$')
                .replace(/\\\)/g, '$');
                
            let sourcesFound = "";
            if (displayContent.includes("\n\nSOURCES: ")) {
                const parts = displayContent.split("\n\nSOURCES: ");
                displayContent = parts[0];
                sourcesFound = parts[1];
            }

            let mathPlaceholders = [];
            displayContent = displayContent.replace(/\$\$([\s\S]*?)\$\$/g, function(match, math) {
                mathPlaceholders.push(`$$${math}$$`);
                return `%%%MATH_${mathPlaceholders.length - 1}%%%`;
            });
            displayContent = displayContent.replace(/(^|[^\\$])\$([^$\n]+)\$/g, function(match, prefix, math) {
                mathPlaceholders.push(`$${math}$`);
                return `${prefix}%%%MATH_${mathPlaceholders.length - 1}%%%`;
            });

            let htmlContent = marked.parse(displayContent);
            mathPlaceholders.forEach((mathStr, index) => {
                // By passing a function, we prevent JS from treating $$ as an escape character for $
                htmlContent = htmlContent.replace(`%%%MATH_${index}%%%`, () => mathStr);
            });

            if (sourcesFound) {
                htmlContent += `<div class="sources-box"><strong><i class="fas fa-book"></i> Sources Used</strong><br>${sourcesFound}</div>`;
            }

            msgDiv.innerHTML = `${header}<div ${bodyClass}>${htmlContent}</div>`;
            
            // Render Math immediately for this historical message
            const innerBody = msgDiv.querySelector('.ai-body');
            renderMathInElement(innerBody, {
                delimiters: [
                    {left: '$$', right: '$$', display: true},
                    {left: '$', right: '$', display: false},
                    {left: '\\(', right: '\\)', display: false},
                    {left: '\\[', right: '\\]', display: true}
                ],
                throwOnError: false
            });
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
    sendBtn.style.display = 'none';
    document.getElementById('stop-btn').style.display = 'inline-block';
    
    currentAbortController = new AbortController();

    // Add user message to UI
    appendMessage('user', message);

    // Add assistant message placeholder as typing indicator
    const assistantMsgDiv = appendMessage('assistant', 'TYPING');
    let fullContent = "";

    try {
        const response = await fetch(`${API_BASE}/chat/stream`, {
            method: 'POST',
            signal: currentAbortController.signal,
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
            
            // Re-added KaTeX preprocessor for professional math representation
            // Normalizing common LLM delimiters [ ] and ( ) to standard LaTeX
            displayContent = displayContent
                .replace(/\\\[/g, '$$$$')
                .replace(/\\\]/g, '$$$$')
                .replace(/\\\(/g, '$')
                .replace(/\\\)/g, '$');

            let sourcesFound = "";
            if (displayContent.includes("\n\nSOURCES: ")) {
                const parts = displayContent.split("\n\nSOURCES: ");
                displayContent = displayContent.split("\n\nSOURCES: ")[0];
                sourcesFound = parts[1];
            }

            // --- PROTECT MATH FROM MARKED ---
            let mathPlaceholders = [];
            
            // Protect block math $$ ... $$
            displayContent = displayContent.replace(/\$\$([\s\S]*?)\$\$/g, function(match, math) {
                mathPlaceholders.push(`$$${math}$$`);
                return `%%%MATH_${mathPlaceholders.length - 1}%%%`;
            });
            // Protect inline math $ ... $
            // (Careful to distinguish between matching $ and random text without spaces)
            displayContent = displayContent.replace(/(^|[^\\$])\$([^$\n]+)\$/g, function(match, prefix, math) {
                mathPlaceholders.push(`$${math}$`);
                return `${prefix}%%%MATH_${mathPlaceholders.length - 1}%%%`;
            });

            // Parse markdown without destroying the math underscores/asterisks!
            let htmlContent = marked.parse(displayContent);

            // --- RESTORE MATH ---
            mathPlaceholders.forEach((mathStr, index) => {
                htmlContent = htmlContent.replace(`%%%MATH_${index}%%%`, () => mathStr);
            });

            bodyEl.innerHTML = htmlContent;
            
            // Trigger KaTeX render
            renderMathInElement(bodyEl, {
                delimiters: [
                    {left: '$$', right: '$$', display: true},
                    {left: '$', right: '$', display: false},
                    {left: '\\(', right: '\\)', display: false},
                    {left: '\\[', right: '\\]', display: true}
                ],
                throwOnError: false
            });
            
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

            // Optimization: Only render circuits every 8 chunks to keep UI responsive
            if (chunkCount % 8 === 0) {
                renderCircuits(bodyEl);
            }

            if (isScrolledToBottom) {
                pane.scrollTop = pane.scrollHeight;
            }
        }
        
        // Final render to ensure everything is perfect
        if (currentChatId === chatIdAtStart) {
            const bodyEl = assistantMsgDiv.querySelector('.ai-body');
            renderMathInElement(bodyEl, {
                delimiters: [
                    {left: '$$', right: '$$', display: true},
                    {left: '$', right: '$', display: false},
                    {left: '\\(', right: '\\)', display: false},
                    {left: '\\[', right: '\\]', display: true}
                ],
                throwOnError: false
            });
            renderCircuits(bodyEl);
        }
    } catch (err) {
        if (err.name === 'AbortError') {
            console.log("Generation stopped by user.");
            // We can leave the partial text as is, just add a small indicator
            const bodyEl = assistantMsgDiv.querySelector('.ai-body');
            bodyEl.innerHTML += `<br><span style="color:#f59e0b; font-size:0.85em;"><i>[Geração Interrompida]</i></span>`;
        } else {
            console.error("Streaming error:", err);
            const errDiv = document.createElement('div');
            errDiv.style.color = '#ef4444';
            errDiv.style.marginTop = '10px';
            errDiv.innerHTML = `<strong><i class="fas fa-exclamation-triangle"></i> Javascript/Stream Error:</strong> ${err.message || err}<br><small>${err.stack || ''}</small>`;
            assistantMsgDiv.querySelector('.ai-body').appendChild(errDiv);
        }
    } finally {
        sendBtn.disabled = false;
        sendBtn.style.display = 'inline-block';
        document.getElementById('stop-btn').style.display = 'none';
        currentAbortController = null;
        input.focus();
        updateTokenBar();
    }
}

function stopGenerating() {
    if (currentAbortController) {
        currentAbortController.abort();
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

// ===== TOKEN USAGE BAR MANAGEMENT =====
let isCompressing = false;
let tokenPollInterval = null;

async function updateTokenBar() {
    if (!currentChatId) {
        const container = document.getElementById('token-bar-container');
        if (container) container.classList.remove('visible');
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/token-usage/${currentChatId}`);
        if (!res.ok) return;
        const data = await res.json();

        const container = document.getElementById('token-bar-container');
        const fill = document.getElementById('token-bar-fill');
        const label = document.getElementById('token-bar-label');
        const countEl = document.getElementById('token-count');
        const statusEl = document.getElementById('token-status');

        if (!container || !fill || !label) return;

        container.classList.add('visible');

        const pct = data.percentage;
        fill.style.width = `${Math.min(pct, 100)}%`;
        label.textContent = `${pct}%`;
        countEl.textContent = `${data.used_tokens.toLocaleString()} / ${data.max_tokens.toLocaleString()} tokens`;

        fill.classList.remove('warning', 'critical');
        statusEl.classList.remove('compressed', 'purging');
        statusEl.textContent = '';

        if (pct >= 80) {
            fill.classList.add('critical');
            statusEl.textContent = '⚠ COMPRESSING...';
            statusEl.classList.add('purging');
            if (!isCompressing) {
                await autoCompress();
            }
        } else if (pct >= 60) {
            fill.classList.add('warning');
            statusEl.textContent = '● HIGH USAGE';
            statusEl.classList.add('compressed');
        }

        if (data.is_compressed && pct < 60) {
            statusEl.textContent = '◆ COMPRESSED';
            statusEl.classList.add('compressed');
        }

    } catch (err) {
        console.error("Token bar update failed:", err);
    }
}

async function autoCompress() {
    if (isCompressing || !currentChatId) return;
    isCompressing = true;
    console.log("[TokenMgr] Starting auto-compression...");

    try {
        const compressRes = await fetch(`${API_BASE}/chat/compress/${currentChatId}`, { method: 'POST' });
        const compressData = await compressRes.json();
        console.log("[TokenMgr] Compression result:", compressData);

        await new Promise(r => setTimeout(r, 500));
        const usageRes = await fetch(`${API_BASE}/token-usage/${currentChatId}`);
        const usageData = await usageRes.json();

        if (usageData.percentage >= 20 && compressData.status === 'compressed') {
            console.log("[TokenMgr] Post-compression usage still high, starting purge cycle...");
            await autoPurge();
        }
    } catch (err) {
        console.error("[TokenMgr] Compression error:", err);
    } finally {
        isCompressing = false;
        await updateTokenBar();
    }
}

async function autoPurge() {
    if (!currentChatId) return;
    let attempts = 0;
    const maxAttempts = 5;

    while (attempts < maxAttempts) {
        attempts++;
        console.log(`[TokenMgr] Purge cycle ${attempts}...`);
        try {
            const purgeRes = await fetch(`${API_BASE}/chat/purge/${currentChatId}`, { method: 'POST' });
            const purgeData = await purgeRes.json();
            if (purgeData.status === 'skip') { console.log("[TokenMgr] Purge skipped."); break; }
            console.log(`[TokenMgr] Purged ${purgeData.removed} messages.`);

            await new Promise(r => setTimeout(r, 300));
            const usageRes = await fetch(`${API_BASE}/token-usage/${currentChatId}`);
            const usageData = await usageRes.json();
            if (usageData.percentage < 20) { console.log("[TokenMgr] Below 20%, done."); break; }
        } catch (err) { console.error("[TokenMgr] Purge error:", err); break; }
    }
}

function startTokenPolling() {
    stopTokenPolling();
    updateTokenBar();
    tokenPollInterval = setInterval(updateTokenBar, 15000);
}

function stopTokenPolling() {
    if (tokenPollInterval) { clearInterval(tokenPollInterval); tokenPollInterval = null; }
}

function convertLatexToMatlab(text) {
    let out = text;
    // Hide block math rendering
    out = out.replace(/\$\$/g, '');
    out = out.replace(/\\\[/g, '');
    out = out.replace(/\\\]/g, '');
    out = out.replace(/\\\(/g, '');
    out = out.replace(/\\\)/g, '');
    // inline dollars
    out = out.replace(/(^|[^\\$\n])\$([^$\n]+)\$/g, '$1$2');

    // Handle fractions
    let oldOut;
    do {
        oldOut = out;
        out = out.replace(/\\frac\s*\{([^{}]+)\}\s*\{([^{}]+)\}/g, '($1)/($2)');
    } while (out !== oldOut);

    // Other symbols
    out = out.replace(/\\cdot/g, '*');
    out = out.replace(/\\times/g, '*');
    out = out.replace(/\\int_\{([^{}]+)\}\^\{([^{}]+)\}/g, 'integral(..., $1, $2)');
    out = out.replace(/\\int/g, 'integral');
    out = out.replace(/\\infty/g, 'inf');
    out = out.replace(/\\left\(/g, '(');
    out = out.replace(/\\right\)/g, ')');
    out = out.replace(/\\left\[/g, '[');
    out = out.replace(/\\right\]/g, ']');
    out = out.replace(/\\,/g, ' ');
    out = out.replace(/\\;/g, ' ');
    out = out.replace(/\\quad/g, ' ');
    out = out.replace(/\\text\{([^{}]+)\}/g, '$1');
    out = out.replace(/\\mathrm\{([^{}]+)\}/g, '$1');
    out = out.replace(/\\_/g, '_');
    
    return out;
}
