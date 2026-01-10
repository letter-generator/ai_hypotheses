const body = document.body;

let textarea, chatHistoryContainer, sendButton, attachButton, newChatButton;
let historyList, fileInput, fileChipContainer, chatTitle, infoButton;
let chatView, infoView;

function getElement(selector, byId = false) {
    return byId ? document.getElementById(selector) : document.querySelector(selector);
}

const API_CONFIG = {
    BASE_URL: 'http://localhost:5000/api',
    HEADERS: {
        'Content-Type': 'application/json',
        'X-User-ID': null
    }
};

const state = {
    chats: [],
    messages: new Map(),
    currentChatId: null,
    ui: { typing: false, sending: false, infoOpen: false },
    attachments: [],
    reviews: [],
    userId: null,
    selectedRating: 0
};

const STORAGE_KEY = 'hypgen_chat_state';

function getOrCreateUserId() {
    let userId = localStorage.getItem('hypgen_user_id');
    if (!userId) {
        userId = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('hypgen_user_id', userId);
    }
    API_CONFIG.HEADERS['X-User-ID'] = userId;
    state.userId = userId;
    return userId;
}

function saveState() {
    try {
        const stateToSave = {
            chats: state.chats,
            messages: Array.from(state.messages.entries())
        };
        localStorage.setItem(STORAGE_KEY, JSON.stringify(stateToSave));
    } catch (e) {
        console.error("Ошибка сохранения:", e);
    }
}

async function loadState() {
    try {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
            const loaded = JSON.parse(stored);
            state.chats = loaded.chats || [];
            state.messages = new Map(loaded.messages || []);
        }
        
        try {
            const serverHistory = await api.loadChatHistory();
            const serverIds = new Set(serverHistory.map(c => c.chat_id));
            const localOnly = state.chats.filter(c => !serverIds.has(c.chat_id));
            state.chats = [...serverHistory, ...localOnly];
            saveState();
        } catch (error) {
            console.warn('Не удалось загрузить историю с сервера');
        }
        
        renderHistory();
    } catch (e) {
        console.error("Ошибка загрузки:", e);
    }
}

const CONFIG = {
    textareaMaxPx: 240
};

const api = {
    async createChat(title) {
        getOrCreateUserId();
        
        const response = await fetch(`${API_CONFIG.BASE_URL}/new_chat`, {
            method: 'POST',
            headers: API_CONFIG.HEADERS,
            body: JSON.stringify({ title: title || 'Новый чат' })
        });
        
        if (!response.ok) {
            throw new Error('Failed to create chat');
        }
        
        const data = await response.json();
        
        const newChat = { chat_id: data.chat_id, title: data.title };
        state.chats.unshift(newChat);
        saveState();
        
        return newChat;
    },

    async sendMessage({ chatId, text, files }) {
        getOrCreateUserId();
        
        const attachmentsPayload = files?.map(f => ({
            name: f.name,
            size: f.size,
            type: f.type || 'unknown'
        })) || [];

        const response = await fetch(`${API_CONFIG.BASE_URL}/send_message`, {
            method: 'POST',
            headers: API_CONFIG.HEADERS,
            body: JSON.stringify({
                chat_id: chatId,
                message: text,
                attachments: attachmentsPayload
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to send message');
        }

        const data = await response.json();
        return { 
            text: data.bot_response.content,
            messageId: data.bot_response.id
        };
    },

    async loadChatHistory() {
        getOrCreateUserId();
        
        const response = await fetch(`${API_CONFIG.BASE_URL}/chat_history`, {
            method: 'GET',
            headers: API_CONFIG.HEADERS
        });
        
        if (!response.ok) {
            console.error('Failed to load chat history');
            return [];
        }
        
        const data = await response.json();
        return data.map(chat => ({
            chat_id: chat.chat_id,
            title: chat.title
        }));
    },

    async loadChatMessages(chatId) {
        getOrCreateUserId();
        
        try {
            const response = await fetch(`${API_CONFIG.BASE_URL}/chat/${chatId}/messages`, {
                method: 'GET',
                headers: API_CONFIG.HEADERS
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: 'Failed to load messages' }));
                throw new Error(errorData.error || `HTTP ${response.status}: Failed to load messages`);
            }
            
            const data = await response.json();
            return data.messages || [];
        } catch (error) {
            console.error('Error loading chat messages:', error);
            return state.messages.get(chatId) || [];
        }
    },

    async submitReview(rating, text) {
        getOrCreateUserId();
        
        const response = await fetch(`${API_CONFIG.BASE_URL}/reviews`, {
            method: 'POST',
            headers: API_CONFIG.HEADERS,
            body: JSON.stringify({ rating, text })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to submit review');
        }
        
        return await response.json();
    },
    
    async loadReviews() {
        getOrCreateUserId();
        
        const response = await fetch(`${API_CONFIG.BASE_URL}/reviews`, {
            method: 'GET',
            headers: API_CONFIG.HEADERS
        });
        
        if (!response.ok) {
            console.error('Failed to load reviews');
            return [];
        }
        
        return await response.json();
    },
    
    async loadReviewStats() {
        getOrCreateUserId();
        
        const response = await fetch(`${API_CONFIG.BASE_URL}/reviews/stats`, {
            method: 'GET',
            headers: API_CONFIG.HEADERS
        });
        
        if (!response.ok) {
            console.error('Failed to load review stats');
            return null;
        }
        
        return await response.json();
    },
    
    async deleteReview(reviewId) {
        getOrCreateUserId();
        
        const response = await fetch(`${API_CONFIG.BASE_URL}/reviews/${reviewId}`, {
            method: 'DELETE',
            headers: API_CONFIG.HEADERS
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to delete review');
        }
        
        return await response.json();
    }
};

function delay(ms) {
    return new Promise(res => setTimeout(res, ms));
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.min(Math.floor(Math.log(bytes) / Math.log(k)), sizes.length - 1);
    const num = bytes / Math.pow(k, i);
    return `${num.toFixed(num >= 10 ? 0 : 1)} ${sizes[i]}`;
}

function autoResizeTextarea() {
    textarea.style.height = 'auto';
    const newHeight = Math.min(textarea.scrollHeight, CONFIG.textareaMaxPx);
    textarea.style.height = `${newHeight}px`;
}

function scrollToBottom() {
    requestAnimationFrame(() => {
        chatHistoryContainer.scrollTop = chatHistoryContainer.scrollHeight;
    });
}

function renderMessages(chatId) {
    chatHistoryContainer.innerHTML = '';
    const fragment = document.createDocumentFragment();
    const list = state.messages.get(chatId) || [];

    list.forEach(msg => {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', `${msg.sender}-message`);
        const parts = [];

        if (msg.attachments?.length) {
            const attachBlock = document.createElement('div');
            attachBlock.className = 'message-attachments';

            msg.attachments.forEach(att => {
                const item = document.createElement('div');
                item.className = 'attachment-chip';
                item.innerHTML = `
                    <div class="attachment-meta">
                        <div class="attachment-name" title="${att.name}">${att.name}</div>
                        <div class="attachment-size">${formatBytes(att.size)}</div>
                    </div>
                `;
                attachBlock.appendChild(item);
            });
            parts.push(attachBlock);
        }

        const textEl = document.createElement('p');
        textEl.className = 'message-text';
        textEl.textContent = msg.text;
        parts.push(textEl);

        parts.forEach(el => messageDiv.appendChild(el));
        fragment.appendChild(messageDiv);
    });

    if (state.ui.typing) {
        const indicator = document.createElement('div');
        indicator.className = 'ai-typing-indicator';
        indicator.innerHTML = `
            <div class="message ai-message typing-indicator">
                <div class="typing-dots">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;
        fragment.appendChild(indicator);
    }

    chatHistoryContainer.appendChild(fragment);
    scrollToBottom();
}

function renderHistory() {
    historyList.innerHTML = '';
    const fragment = document.createDocumentFragment();

    state.chats.forEach(chat => {
        const item = document.createElement('a');
        item.href = `/chat/${chat.chat_id}`;
        item.className = 'history-item';
        item.dataset.chatId = chat.chat_id;
        item.textContent = truncateTitle(chat.title);
        if (state.currentChatId === chat.chat_id) {
            item.classList.add('active');
        }
        item.addEventListener('click', onHistoryClick);
        fragment.appendChild(item);
    });

    historyList.appendChild(fragment);
}

function truncateTitle(title) {
    const MAX_TITLE_LENGTH = 30;
    let t = title.replace(/\s+/g, ' ').trim();
    if (!t) return 'Новый чат';
    if (t.length <= MAX_TITLE_LENGTH) return t;
    const temp = t.slice(0, MAX_TITLE_LENGTH).trim();
    const lastSpace = temp.lastIndexOf(' ');
    return (lastSpace > 0 ? temp.slice(0, lastSpace) : temp) + '...';
}

function renderFileChips() {
    fileChipContainer.innerHTML = '';
    if (!state.attachments.length) {
        fileChipContainer.style.display = 'none';
        return;
    }

    const fragment = document.createDocumentFragment();
    state.attachments.forEach((file, index) => {
        const chip = document.createElement('div');
        chip.className = 'file-chip';
        chip.innerHTML = `
            <span class="file-chip-text" title="${file.name}">${file.name}</span>
            <button class="file-chip-delete" data-index="${index}" aria-label="Удалить файл">×</button>
        `;
        fragment.appendChild(chip);
    });

    fileChipContainer.appendChild(fragment);
    fileChipContainer.style.display = 'flex';

    fileChipContainer.querySelectorAll('.file-chip-delete').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const idx = Number(e.currentTarget.dataset.index);
            state.attachments.splice(idx, 1);
            renderFileChips();
        });
    });
}

function activateChatMode() {
    body.classList.add('chat-active');
    closeInfoView();
}

function activateStartMode() {
    body.classList.remove('chat-active');
    state.currentChatId = null;
    state.ui.typing = false;
    state.ui.sending = false;
    state.attachments = [];
    chatTitle.textContent = 'Новый чат';
    chatHistoryContainer.innerHTML = '';
    fileInput.value = '';
    renderFileChips();
    autoResizeTextarea();
    textarea.value = '';
    textarea.focus();
    renderHistory();
    closeInfoView();
}

function upsertChat(chat) {
    const exists = state.chats.find(c => c.chat_id === chat.chat_id);
    if (!exists) {
        state.chats.unshift(chat);
    }
}

function pushMessage(chatId, message) {
    const list = state.messages.get(chatId) || [];
    list.push(message);
    state.messages.set(chatId, list);
}

async function handleSend(e) {
    if (e) {
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();
    }
    
    if (state.ui.sending) return false;
    if (!textarea) return false;

    const text = textarea.value.trim();
    const files = [...state.attachments];
    if (!text && !files.length) return false;

    const attachmentsPayload = files.map(f => ({
        name: f.name,
        size: f.size,
        type: (f.type || '').toUpperCase()
    }));

    state.ui.sending = true;
    textarea.value = '';
    fileInput.value = '';
    state.attachments = [];
    renderFileChips();
    autoResizeTextarea();

    if (!state.currentChatId) {
        try {
            const chat = await api.createChat(text);
            state.currentChatId = chat.chat_id;
            chatTitle.textContent = chat.title;
            upsertChat(chat);
            activateChatMode();
            renderHistory();
        } catch (error) {
            console.error('Ошибка создания чата:', error);
            state.ui.sending = false;
            return false;
        }
    }

    const chatId = state.currentChatId;
    
    pushMessage(chatId, {
        id: 'temp_' + Date.now(),
        sender: 'user',
        text,
        ts: Date.now(),
        attachments: attachmentsPayload
    });
    renderMessages(chatId);

    state.ui.typing = true;
    renderMessages(chatId);

    try {
        const resp = await api.sendMessage({ chatId, text, files });
        state.ui.typing = false;
        
        pushMessage(chatId, {
            id: resp.messageId || crypto.randomUUID(),
            sender: 'ai',
            text: resp.text,
            ts: Date.now()
        });
        
        try {
            const serverMessages = await api.loadChatMessages(chatId);
            if (serverMessages && serverMessages.length > 0) {
                state.messages.set(chatId, serverMessages);
            }
        } catch (syncError) {
        }
        
        renderMessages(chatId);
        saveState();
    } catch (err) {
        console.error('Ошибка отправки', err);
        state.ui.typing = false;
        pushMessage(chatId, {
            id: 'error_' + Date.now(),
            sender: 'ai',
            text: 'Ошибка отправки. Попробуйте ещё раз.',
            ts: Date.now()
        });
        renderMessages(chatId);
    } finally {
        state.ui.sending = false;
        textarea.focus();
    }
    
    return false;
}

async function onHistoryClick(e) {
    e.preventDefault();
    const chatId = Number(e.currentTarget.dataset.chatId);
    if (!chatId) return;
    
    closeInfoView();
    state.currentChatId = chatId;
    chatTitle.textContent = truncateTitle(state.chats.find(c => c.chat_id === chatId)?.title || 'Чат');
    activateChatMode();
    renderHistory();
    
    try {
        const messages = await api.loadChatMessages(chatId);
        state.messages.set(chatId, messages);
        renderMessages(chatId);
    } catch (error) {
        console.error('Ошибка загрузки сообщений:', error);
        renderMessages(chatId);
    }
    
    textarea.focus();
}

function handleFiles(files) {
    Array.from(files).forEach(file => {
        const exists = state.attachments.some(f => f.name === file.name && f.size === file.size);
        if (!exists) state.attachments.push(file);
    });
    renderFileChips();
}

function openInfoView() {
    state.ui.infoOpen = true;
    chatView.setAttribute('aria-hidden', 'true');
    infoView.setAttribute('aria-hidden', 'false');
    body.classList.add('info-mode');
}

function closeInfoView() {
    state.ui.infoOpen = false;
    chatView.setAttribute('aria-hidden', 'false');
    infoView.setAttribute('aria-hidden', 'true');
    body.classList.remove('info-mode');
    textarea.focus();
}

function initUser() {
    getOrCreateUserId();
    const userLabel = document.querySelector('.review-user');
    if (userLabel) userLabel.textContent = `Пользователь_${state.userId.substring(0, 8)}`;
}

function initStarRating() {
    const stars = document.querySelectorAll('#rating-picker .star');
    stars.forEach((star, index) => {
        star.addEventListener('click', () => {
            state.selectedRating = index + 1;
            stars.forEach((s, i) => {
                s.classList.toggle('active', i <= index);
            });
        });
    });
}

async function handleReviewSubmit(e) {
    if (e) {
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();
    }
    
    const reviewInput = document.getElementById('review-text');
    if (!reviewInput) return false;
    
    const text = reviewInput.value.trim();
    if (!text || state.selectedRating === 0) {
        alert('Пожалуйста, укажите рейтинг и введите текст отзыва.');
        return false;
    }

    try {
        const newReview = await api.submitReview(state.selectedRating, text);
        state.reviews.unshift({
            id: newReview.id,
            userId: newReview.user_id,
            rating: newReview.rating,
            text: newReview.text,
            created_at: newReview.created_at
        });
        
        await renderReviews();
        await updateReviewStats();
        
        reviewInput.value = '';
        state.selectedRating = 0;
        document.querySelectorAll('#rating-picker .star').forEach(s => s.classList.remove('active'));
        
    } catch (error) {
        console.error('Ошибка при отправке отзыва:', error);
        alert('Не удалось отправить отзыв. Попробуйте ещё раз.');
    }
    
    return false;
}

async function renderReviews() {
    const list = document.querySelector('.reviews-list');
    if (!list) return;
    
    list.innerHTML = '';
    
    const sortedReviews = [...state.reviews].sort((a, b) => 
        new Date(b.created_at || 0) - new Date(a.created_at || 0)
    );
    
    sortedReviews.forEach(rev => {
        const isMine = String(rev.userId) === String(state.userId);
        const item = document.createElement('div');
        item.className = 'review-item';
        
        let dateStr = '';
        if (rev.created_at) {
            const date = new Date(rev.created_at);
            dateStr = date.toLocaleDateString('ru-RU', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric'
            });
        }
        
        item.innerHTML = `
            <div class="review-header">
                <div class="review-user">
                    Пользователь_${rev.userId} ${isMine ? '<span class="my-label">(Вы)</span>' : ''}
                    ${dateStr ? `<span class="review-date">${dateStr}</span>` : ''}
                </div>
                ${isMine ? `<button class="delete-review-btn" onclick="deleteReview(${rev.id})" data-review-id="${rev.id}">Удалить отзыв</button>` : ''}
            </div>
            <div class="review-stars small">${'★'.repeat(rev.rating)}${'☆'.repeat(5-rev.rating)}</div>
            <div class="review-body">${rev.text}</div>
        `;
        list.appendChild(item);
        
        const divider = document.createElement('div');
        divider.className = 'review-divider';
        list.appendChild(divider);
    });
}

window.deleteReview = async function(reviewId) {
    if (!confirm('Вы уверены, что хотите удалить этот отзыв?')) {
        return;
    }
    
    try {
        await api.deleteReview(reviewId);
        state.reviews = state.reviews.filter(r => r.id !== reviewId);
        await renderReviews();
        await updateReviewStats();
    } catch (error) {
        console.error('Ошибка при удалении отзыва:', error);
        alert('Не удалось удалить отзыв.');
    }
};

async function updateReviewStats() {
    try {
        const stats = await api.loadReviewStats();
        if (!stats) return;
        
        const scoreDisplay = document.querySelector('.score-main');
        if (scoreDisplay) {
            scoreDisplay.textContent = stats.average_rating.toFixed(1).replace('.', ',');
        }
        
        for (let i = 1; i <= 5; i++) {
            const bar = document.getElementById(`bar-${i}`);
            if (bar && stats.distribution[i] !== undefined) {
                const percentage = stats.total_reviews > 0 ? 
                    (stats.distribution[i] / stats.total_reviews) * 100 : 0;
                bar.style.width = percentage + '%';
            }
        }
    } catch (error) {
        console.error('Ошибка при загрузке статистики:', error);
    }
}

function saveReviewsToStorage() {
    localStorage.setItem('hypgen_reviews', JSON.stringify(state.reviews));
}

function loadReviewsFromStorage() {
    const saved = localStorage.getItem('hypgen_reviews');
    if (saved) state.reviews = JSON.parse(saved);
}

document.addEventListener('DOMContentLoaded', async () => {
    textarea = getElement('.chat-textarea');
    chatHistoryContainer = getElement('.chat-history-container');
    sendButton = document.querySelector('.send-button:not(.review-send-btn)');
    attachButton = getElement('.attach-button');
    newChatButton = getElement('new-chat-btn', true);
    historyList = getElement('.history-list');
    fileInput = getElement('file-input', true);
    fileChipContainer = getElement('.file-chip-container');
    chatTitle = getElement('.chat-title');
    infoButton = getElement('.info-button');
    chatView = getElement('.chat-view');
    infoView = getElement('.info-view');
    
    if (textarea) {
        textarea.addEventListener('input', autoResizeTextarea);
        textarea.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                e.stopPropagation();
                handleSend(e);
            }
        }, { passive: false });
    }

    if (sendButton) {
        sendButton.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            handleSend(e);
        }, { passive: false, capture: true });
    }

    if (newChatButton) {
        newChatButton.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            activateStartMode();
        }, { passive: false, capture: true });
    }

    if (attachButton && fileInput) {
        attachButton.addEventListener('click', (e) => {
            e.preventDefault();
            fileInput.click();
        }, { passive: false });
    }

    if (fileInput) {
        fileInput.addEventListener('change', () => handleFiles(fileInput.files));
    }

    if (infoButton) {
        infoButton.addEventListener('click', (e) => {
            e.preventDefault();
            openInfoView();
        }, { passive: false });
    }
    
    autoResizeTextarea();
    activateStartMode();
    
    const submitBtn = document.getElementById('submit-review');
    const reviewInput = document.getElementById('review-text');

    if (submitBtn) {
        submitBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            handleReviewSubmit(e);
        }, { passive: false });
    }

    if (reviewInput) {
        reviewInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                handleReviewSubmit(e);
            }
        }, { passive: false });
    }
    
    initUser();
    initStarRating();
    
    try {
        const serverReviews = await api.loadReviews();
        state.reviews = serverReviews;
        await renderReviews();
        await updateReviewStats();
    } catch (error) {
        console.error('Ошибка при загрузке отзывов:', error);
        loadReviewsFromStorage();
        renderReviews();
    }
});

loadState();
renderHistory();
activateStartMode();