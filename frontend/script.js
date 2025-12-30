// Базовые DOM-ссылки
const body = document.body;
const textarea = document.querySelector('.chat-textarea');
const chatHistoryContainer = document.querySelector('.chat-history-container');
const sendButton = document.querySelector('.send-button');
const attachButton = document.querySelector('.attach-button');
const newChatButton = document.querySelector('.nav-button[href="/new-chat"]');
const historyList = document.querySelector('.history-list');
const fileInput = document.getElementById('file-input');
const fileChipContainer = document.querySelector('.file-chip-container');
const chatTitle = document.querySelector('.chat-title');
const infoButton = document.querySelector('.info-button');
const chatView = document.querySelector('.chat-view');
const infoView = document.querySelector('.info-view');

const API_CONFIG = {
    BASE_URL: 'http://localhost:5000/api',
    HEADERS: {
        'Content-Type': 'application/json',
        'X-User-ID': null
    }
};

// Глобальное состояние
const state = {
    chats: [],
    messages: new Map(), // chatId -> [{id, sender, text, ts, attachments?}]
    currentChatId: null,
    ui: { typing: false, sending: false, infoOpen: false },
    attachments: [],
    reviews: [],
    userId: null,
    selectedRating: 0
};

// Ключ для локального хранилища
const STORAGE_KEY = 'hypgen_chat_state';

// Генерация/получение ID пользователя из localStorage
function getOrCreateUserId() {
    let userId = localStorage.getItem('hypgen_user_id');
    if (!userId) {
        userId = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('hypgen_user_id', userId);
    }
    API_CONFIG.HEADERS['X-User-ID'] = userId;
    return userId;
}

// Сохранение состояния
function saveState() {
    // LocalStorage может хранить только строки, поэтому конвертируем Map в массив для сохранения
    const stateToSave = {
        chats: state.chats,
        messages: Array.from(state.messages.entries()) // конвертируем Map в массив
    };

    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(stateToSave));
    } catch (e) {
        console.error("Ошибка сохранения в LocalStorage:", e);
    }
}

// Загрузка состояния
async function loadState() {
    try {
        const storedState = localStorage.getItem(STORAGE_KEY);
        if (storedState) {
            const loadedState = JSON.parse(storedState);
            state.chats = loadedState.chats || [];
            state.messages = new Map(loadedState.messages || []);
        }
        
        // Дополнительно загружаем историю с сервера
        try {
            const serverHistory = await api.loadChatHistory();
            // Объединяем локальную и серверную историю
            const serverIds = new Set(serverHistory.map(c => c.chat_id));
            
            // Добавляем только те чаты, которых нет на сервере
            const localOnlyChats = state.chats.filter(c => !serverIds.has(c.chat_id));
            state.chats = [...serverHistory, ...localOnlyChats];
            
            saveState(); // Сохраняем объединённое состояние
        } catch (error) {
            console.warn('Could not load server history:', error);
        }
        
        renderHistory();
    } catch (e) {
        console.error("Ошибка загрузки из LocalStorage:", e);
    }
}

const CONFIG = {
    textareaMaxPx: 240
};

// Mock API-слой
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
        
        // Сохраняем в локальное состояние
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
        
        const response = await fetch(`${API_CONFIG.BASE_URL}/chat/${chatId}/messages`, {
            method: 'GET',
            headers: API_CONFIG.HEADERS
        });
        
        if (!response.ok) {
            throw new Error('Failed to load messages');
        }
        
        const data = await response.json();
        return data.messages;
    }
};

// Утилиты
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

// Рендер сообщений
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

// Рендер истории
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

// Рендер файловых чипов
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

// Управление режимами
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

// Сервисные функции
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

// Обработчики
async function handleSend() {
    if (state.ui.sending) return;

    const text = textarea.value.trim();
    const files = [...state.attachments];
    if (!text && !files.length) return;

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
            console.error('Error creating chat:', error);
            state.ui.sending = false;
            return;
        }
    }

    const chatId = state.currentChatId;
    
    // Локальное сохранение сообщения пользователя
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
        
        // Сохраняем ответ AI
        pushMessage(chatId, {
            id: resp.messageId || crypto.randomUUID(),
            sender: 'ai',
            text: resp.text,
            ts: Date.now()
        });
        
        // Синхронизируем с сервером (загружаем все сообщения заново для гарантии)
        const serverMessages = await api.loadChatMessages(chatId);
        state.messages.set(chatId, serverMessages);
        
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
        // Загружаем сообщения с сервера
        const messages = await api.loadChatMessages(chatId);
        state.messages.set(chatId, messages);
        renderMessages(chatId);
    } catch (error) {
        console.error('Error loading messages:', error);
        // Показываем сообщения из кэша
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

// Инфо-вид
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

// Привязка событий
textarea.addEventListener('input', autoResizeTextarea);
textarea.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
    }
});

sendButton.addEventListener('click', handleSend);

newChatButton.addEventListener('click', (e) => {
    e.preventDefault();
    activateStartMode();
});

attachButton.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', () => handleFiles(fileInput.files));

infoButton.addEventListener('click', () => openInfoView());

// Инициализация
document.addEventListener('DOMContentLoaded', async () => {
    autoResizeTextarea();
    activateStartMode();
    
    const submitBtn = document.getElementById('submit-review');
    const reviewInput = document.getElementById('review-text');

    if (submitBtn) {
        submitBtn.onclick = handleReviewSubmit;
    }

    if (reviewInput) {
        reviewInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault(); 
                handleReviewSubmit();
            }
        });
    }
});

// инициализация пользователя (при загрузке страницы)
function initUser() {
    let id = localStorage.getItem('hypgen_user_id');
    if (!id) {
        id = Math.floor(1000 + Math.random() * 9000); // Порядковый номер
        localStorage.setItem('hypgen_user_id', id);
    }
    state.userId = id;
    const userLabel = document.querySelector('.review-user');
    if (userLabel) userLabel.textContent = `Пользователь_${id}`;
}

// выбор звезд
function initStarRating() {
    const stars = document.querySelectorAll('#rating-picker .star');
    stars.forEach((star, index) => {
        star.addEventListener('click', () => {
            // Устанавливаем рейтинг (индекс + 1, так как индекс начинается с 0)
            state.selectedRating = index + 1; 
            
            // Подсвечиваем звезды
            stars.forEach((s, i) => {
                s.classList.toggle('active', i <= index);
            });
            console.log("Выбранный рейтинг:", state.selectedRating); // Для проверки в консоли
        });
    });
}

document.getElementById('review-text').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        handleReviewSubmit();
    }
});

// отправка отзыва
function handleReviewSubmit() {
    const reviewInput = document.getElementById('review-text');
    const text = reviewInput.value.trim();
    
    // Проверяем именно текущее состояние
    if (!text || state.selectedRating === 0) {
        alert('Пожалуйста, укажите рейтинг и введите текст отзыва.');
        return;
    }

    // Если всё ок, создаем отзыв
    const newReview = {
        id: Date.now(),
        userId: state.userId,
        rating: state.selectedRating,
        text: text
    };

    state.reviews.push(newReview);
    saveReviewsToStorage();
    renderReviews();

    // Очистка после успешной отправки
    reviewInput.value = '';
    state.selectedRating = 0;
    
    // Снимаем подсветку со звезд
    document.querySelectorAll('#rating-picker .star').forEach(s => s.classList.remove('active'));
}

// рендер списка
function renderReviews() {
    const list = document.querySelector('.reviews-list');
    if (!list) return;
    
    list.innerHTML = '';
    state.reviews.forEach(rev => {
        const isMine = String(rev.userId) === String(state.userId);
        const item = document.createElement('div');
        item.className = 'review-item';
        
        // Формируем шапку отзыва: Ник + (Вы) + Кнопка удаления
        item.innerHTML = `
            <div class="review-header">
                <div class="review-user">
                    Пользователь_${rev.userId} ${isMine ? '<span class="my-label">(Вы)</span>' : ''}
                </div>
                ${isMine ? `<button class="delete-review-btn" onclick="deleteReview(${rev.id})">Удалить отзыв</button>` : ''}
            </div>
            <div class="review-stars small">${'★'.repeat(rev.rating)}</div>
            <div class="review-body">${rev.text}</div>
        `;
        list.appendChild(item);
        
        const divider = document.createElement('div');
        divider.className = 'review-divider';
        list.appendChild(divider);
    });
    
    updateAverageScore();
}

window.deleteReview = function(id) {
    state.reviews = state.reviews.filter(r => r.id !== id);
    saveReviewsToStorage();
    renderReviews();
};

// Сохранение именно отзывов
function saveReviewsToStorage() {
    localStorage.setItem('hypgen_reviews', JSON.stringify(state.reviews));
}

function loadReviewsFromStorage() {
    const saved = localStorage.getItem('hypgen_reviews');
    if (saved) state.reviews = JSON.parse(saved);
}

function updateAverageScore() {
    const scoreDisplay = document.querySelector('.score-main');
    if (!scoreDisplay) return;

    // Если отзывов нет
    if (state.reviews.length === 0) {
        scoreDisplay.textContent = "0,0";
        for (let i = 1; i <= 5; i++) {
            const bar = document.getElementById(`bar-${i}`);
            if (bar) bar.style.width = '0%';
        }
        return;
    }

    // Считаем средний балл
    const totalScore = state.reviews.reduce((acc, r) => acc + r.rating, 0);
    const avg = totalScore / state.reviews.length;
    scoreDisplay.textContent = avg.toFixed(1).replace('.', ',');

    // Сколько каких оценок
    const distribution = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 };
    state.reviews.forEach(rev => {
        distribution[rev.rating]++;
    });

    // Обновляем ширину полосок
    for (let i = 1; i <= 5; i++) {
        const bar = document.getElementById(`bar-${i}`);
        if (bar) {
            // Процент = (кол-во конкретных оценок / общее кол-во отзывов) * 100
            const percentage = (distribution[i] / state.reviews.length) * 100;
            bar.style.width = percentage + '%';
        }
    }
}

loadState();
renderHistory();
activateStartMode();
initUser();
initStarRating();
loadReviewsFromStorage();
renderReviews();
document.querySelector('.review-send').onclick = handleReviewSubmit;