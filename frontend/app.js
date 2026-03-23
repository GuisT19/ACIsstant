const API_BASE = "http://localhost:8000/api";
let currentChatId = null;
let currentLanguage = "en-US";

// --- Initializing UI ---
document.addEventListener('DOMContentLoaded', () => {
    loadChatList();
    
    // Auto-resize textarea
    const userInput = document.getElementById('user-input');
    userInput.addEventListener('input', function() {
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
    marked.setOptions({
        highlight: function(code, lang) {
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
            item.innerHTML = `<i class="far fa-comment-dots"></i> ${chat.title}`;
            item.onclick = () => loadChat(chat.id, chat.title);
            list.appendChild(item);
        });
    } catch (err) {
        console.error("Failed to load chats:", err);
    }
}

async function createNewChat() {
    const title = prompt("Chat Title:", "New Study Session");
    if (!title) return;
    
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
    } catch (err) {
        console.error("Failed to create chat:", err);
    }
}

async function loadChat(chatId, title) {
    currentChatId = chatId;
    document.getElementById('current-chat-title').innerText = title;
    
    // Update active state in sidebar
    document.querySelectorAll('.chat-item').forEach(el => {
        el.classList.remove('active');
        // Check for matching title in innerHTML text content
        if (el.textContent.includes(title)) el.classList.add('active');
    });

    const messagesPane = document.getElementById('chat-messages');
    messagesPane.innerHTML = '<div class="loader">Loading messages...</div>';
    
    try {
        const res = await fetch(`${API_BASE}/chats/${chatId}/messages`);
        const messages = await res.json();
        messagesPane.innerHTML = '';
        
        if (messages.length === 0) {
            messagesPane.innerHTML = `<div class="welcome-screen"><h2>Chat Started: ${title}</h2><p>I am ready to help with your questions.</p></div>`;
        } else {
            messages.forEach(msg => appendMessage(msg.role, msg.content));
        }
    } catch (err) {
        console.error("Failed to load messages:", err);
        messagesPane.innerHTML = 'Error loading messages.';
    }
}

function appendMessage(role, content) {
    const pane = document.getElementById('chat-messages');
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}`;
    
    if (role === 'assistant') {
        msgDiv.innerHTML = marked.parse(content);
    } else {
        msgDiv.innerText = content;
    }
    
    pane.appendChild(msgDiv);
    pane.scrollTop = pane.scrollHeight;
    return msgDiv;
}

async function sendMessage() {
    const input = document.getElementById('user-input');
    const message = input.value.trim();
    if (!message || !currentChatId) return;

    input.value = '';
    input.style.height = 'auto';
    
    // Add user message to UI
    appendMessage('user', message);
    
    // Add assistant message placeholder
    const assistantMsgDiv = appendMessage('assistant', '');
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

        if (!response.body) throw new Error("No response body");

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value, { stream: true });
            fullContent += chunk;
            assistantMsgDiv.innerHTML = marked.parse(fullContent);
            document.getElementById('chat-messages').scrollTop = document.getElementById('chat-messages').scrollHeight;
        }
    } catch (err) {
        console.error("Streaming error:", err);
        assistantMsgDiv.innerText = "Error processing response.";
    }
}

function updateLanguage() {
    currentLanguage = document.getElementById('lang-select').value;
}

function quickAction(text) {
    document.getElementById('user-input').value = text;
    if (!currentChatId) {
        // Automatically create a chat if none exists
        document.querySelector('.new-chat-btn').click();
    }
}
