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
        loadChat(data.chat_id, data.title);
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
            messagesPane.innerHTML = `<div class="welcome-screen"><h2>Chat started: ${title}</h2><p>I am ready for your questions.</p></div>`;
        } else {
            messages.forEach(msg => appendMessage(msg.role, msg.content));
        }
        renderMathInPane(messagesPane);
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
                { left: "\\[", right: "\\]", display: true }
            ],
            throwOnError: false
        });
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

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            fullContent += chunk;

            if (isFirstChunk) {
                // Clear the typing indicator
                assistantMsgDiv.querySelector('.ai-body').innerHTML = '';
                isFirstChunk = false;
            }

            const pane = document.getElementById('chat-messages');
            // Check if user is already near the bottom before auto-scrolling
            const isScrolledToBottom = pane.scrollHeight - pane.clientHeight <= pane.scrollTop + 80;

            const bodyEl = assistantMsgDiv.querySelector('.ai-body');
            bodyEl.innerHTML = marked.parse(fullContent);
            renderMathInPane(bodyEl);

            if (isScrolledToBottom) {
                pane.scrollTop = pane.scrollHeight;
            }
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
