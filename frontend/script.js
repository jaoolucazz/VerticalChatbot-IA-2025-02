const messages = document.getElementById('messages');
const form = document.getElementById('chat-form');
const input = document.getElementById('input-text');
const statusDot = document.getElementById('status-dot');
const statusText = document.getElementById('status-text');

const API_URL = 'http://127.0.0.1:5000';

// testa conexão
async function checkHealth() {
    try {
        const res = await fetch(`${API_URL}/`);
        if (res.ok) {
            statusDot.className = 'status-dot online';
            statusText.textContent = 'Sistema Online';
            statusText.style.color = '#1DB954';
            return true;
        }
    } catch (err) {
        statusDot.className = 'status-dot offline';
        statusText.textContent = 'Servidor Offline';
        statusText.style.color = '#ef4444';
        return false;
    }
}
setInterval(checkHealth, 5000);
checkHealth();

// funções utilitárias
function safeRefreshIcons() {
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

function safeRemove(elementId) {
    const el = document.getElementById(elementId);
    if (el) el.remove();
}

function scrollToBottom() {
    messages.scrollTo({ top: messages.scrollHeight, behavior: 'smooth' });
}

function addMessage(text, sender) {
    const div = document.createElement('div');
    div.className = `msg ${sender}`;
    div.innerHTML = `
        <div class="avatar"><i data-lucide="${sender === 'bot' ? 'bot' : 'user'}"></i></div>
        <div class="bubble">${text}</div>
    `;
    messages.appendChild(div);
    safeRefreshIcons();
    scrollToBottom();
}

function addSpotify(id, title) {
    const div = document.createElement('div');
    div.className = 'msg bot';
    
    div.innerHTML = `
        <div class="avatar" style="opacity:0"></div>
        <div class="spotify-embed" style="display:flex; justify-content:center;">
            <iframe 
                src="https://open.spotify.com/embed/playlist/${id}?utm_source=generator&theme=0" 
                style="width:900px; max-width:100%; height:480px; border:0;" 
                allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" 
                loading="lazy">
            </iframe>
        </div>
    `;
    messages.appendChild(div);
    scrollToBottom();
}

// envio de mensagens
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;

    addMessage(text, 'user');
    input.value = '';
    input.focus();

    const loadingId = 'loader-' + Date.now();
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'msg bot';
    loadingDiv.id = loadingId;
    loadingDiv.innerHTML = `
        <div class="avatar"><i data-lucide="bot"></i></div>
        <div class="bubble" style="color: #888;">A analisar...</div>
    `;
    messages.appendChild(loadingDiv);
    safeRefreshIcons();
    scrollToBottom();

    try {
        const res = await fetch(`${API_URL}/api/recommend`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });

        safeRemove(loadingId);

        if (!res.ok) throw new Error('Erro na API');
        const data = await res.json();

        // 🔥 SUPORTE A MÚLTIPLAS PLAYLISTS
        if (data.multiple) {
            for (const item of data.results) {
                addMessage(item.message, 'bot');

                if (item.found) {
                    addSpotify(item.spotify_id, item.title);
                }
            }
        }
        else if (data.found) {
            addMessage(data.message, 'bot');
            addSpotify(data.spotify_id, data.title);
        }
        else {
            addMessage(data.message || "Não entendi.", 'bot');
        }

    } catch (err) {
        safeRemove(loadingId);
        addMessage("⚠️ Erro de conexão. O Backend está rodando?", 'bot');
        checkHealth();
    }
});
