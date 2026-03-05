// ── Digitally Agency — AI Chat Module ────────────────────────────────────────

let chatHistory = [];
let chatOpen = false;

function toggleChat() {
    chatOpen = !chatOpen;
    const panel = document.getElementById('chat-panel');
    if (panel) {
        panel.className = chatOpen ? 'chat-panel open' : 'chat-panel';
        if (chatOpen) {
            track('chat_opened');
            const input = document.getElementById('chat-in');
            if (input) input.focus();
        }
    }
}

async function sendChat(apiBase = '', context = {}) {
    const inp = document.getElementById('chat-in');
    const text = inp ? inp.value.trim() : '';
    if (!text) return;

    inp.value = '';
    addMsg(text, 'user');
    chatHistory.push({ role: 'user', content: text });

    const typing = addMsg('···', 'bot typing');

    try {
        const r = await fetch(`${apiBase}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ messages: chatHistory, context: context })
        });
        const d = await r.json();
        if (typing) typing.remove();

        const reply = d.ok ? d.reply : 'Sorry, I hit an error. Make sure your AI API key is set.';
        addMsg(reply, 'bot');
        chatHistory.push({ role: 'assistant', content: reply });
    } catch (e) {
        if (typing) typing.remove();
        addMsg('Connection error — is the backend running?', 'bot');
    }
}

function addMsg(text, cls) {
    const div = document.createElement('div');
    div.className = `msg ${cls}`;
    div.textContent = text;
    const msgs = document.getElementById('chat-msgs');
    if (msgs) {
        msgs.appendChild(div);
        msgs.scrollTop = msgs.scrollHeight;
    }
    return div;
}

// Initial Listener
document.addEventListener('DOMContentLoaded', () => {
    const chatIn = document.getElementById('chat-in');
    if (chatIn) {
        chatIn.addEventListener('keydown', e => {
            if (e.key === 'Enter') sendChat();
        });
    }
});
