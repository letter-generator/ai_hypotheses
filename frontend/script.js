
// КОНСОЛИДАЦИЯ ЭЛЕМЕНТОВ DOM И ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ
const body = document.body;
const textarea = document.querySelector('.chat-textarea');
const chatHistoryContainer = document.querySelector('.chat-history-container');
const aiTypingIndicator = document.querySelector('.ai-typing-indicator');

// Кнопки и навигация
const sendButton = document.querySelector('.send-button');
const attachButton = document.querySelector('.attach-button');
const newChatButton = document.querySelector('.nav-button[href="/new-chat"]');
const historyList = document.querySelector('.history-list');

// Логика прикрепления файлов
const fileInput = document.getElementById('file-input');
const fileChipContainer = document.querySelector('.file-chip-container');
let attachedFiles = [];

// Настройки
const MAX_HEIGHT = 200;
window.currentChatId = null;
let chatIdCounter = 3;

// 2. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ

function autoResizeTextarea() {
    textarea.style.height = 'auto';
    const newHeight = Math.min(textarea.scrollHeight, MAX_HEIGHT);
    textarea.style.height = newHeight + 'px';
}

function scrollToBottom() {
    requestAnimationFrame(() => {
        chatHistoryContainer.scrollTop = chatHistoryContainer.scrollHeight;
    });
}

/**
 * Создает и добавляет сообщение в историю чата.
 * @param {string} sender - 'user' или 'ai'
 * @param {string} text - Текст сообщения
 */
function createMessage(sender, text) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', `${sender}-message`);
    messageDiv.innerHTML = `<p class="message-text">${text}</p>`;

    chatHistoryContainer.appendChild(messageDiv);

    scrollToBottom();
}

/**
 * Показывает индикатор печати AI.
 */
function showTypingIndicator() {
    // Удаляем старый индикатор если есть
    const oldIndicator = chatHistoryContainer.querySelector('.ai-typing-indicator');
    if (oldIndicator) {
        oldIndicator.remove();
    }

    // Создаем новый индикатор
    const indicatorHTML = `
        <div class="ai-typing-indicator">
            <div class="message ai-message typing-indicator">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        </div>
    `;

    // Добавляем индикатор в КОНЕЦ контейнера
    chatHistoryContainer.insertAdjacentHTML('beforeend', indicatorHTML);

    // Получаем новый элемент индикатора
    const newIndicator = chatHistoryContainer.querySelector('.ai-typing-indicator');
    newIndicator.style.display = 'flex';

    scrollToBottom();
}

/**
 * Скрывает индикатор печати AI.
 */
function hideTypingIndicator() {
    const indicator = chatHistoryContainer.querySelector('.ai-typing-indicator');
    if (indicator) {
        indicator.remove();
    }
}

/**
 * Удаляет все чипы файлов и очищает массив прикрепленных файлов.
 */
function clearAttachedFiles() {
    attachedFiles = [];
    fileInput.value = '';
    renderFileChips();
}

/**
 * Отображает чипы прикрепленных файлов.
 */
function renderFileChips() {
    fileChipContainer.innerHTML = '';

    if (attachedFiles.length === 0) {
        fileChipContainer.style.display = 'none';
        return;
    }

    attachedFiles.forEach((file, index) => {
        const chipHTML = `
            <div class="file-chip">
                <span class="file-chip-text" title="${file.name}">${file.name}</span>
                <button class="file-chip-delete" data-index="${index}">×</button>
            </div>
        `;
        fileChipContainer.innerHTML += chipHTML;
    });

    fileChipContainer.style.display = 'flex';

    // Привязываем обработчики к кнопкам удаления
    fileChipContainer.querySelectorAll('.file-chip-delete').forEach(button => {
        button.addEventListener('click', (e) => {
            const indexToRemove = parseInt(e.currentTarget.dataset.index);
            attachedFiles.splice(indexToRemove, 1);
            renderFileChips();
        });
    });
}

/**
 * Создает новый элемент в списке истории чатов.
 * @param {number} chatId - ID нового чата
 * @param {string} title - Текст для заголовка чата
 */
function createHistoryItem(chatId, title) {
    const newHistoryItem = document.createElement('a');
    const MAX_TITLE_LENGTH = 30;

    // Усечение текста
    let truncatedTitle = title.replace(/\s+/g, ' ').trim();
    if (truncatedTitle.length > MAX_TITLE_LENGTH) {
        let tempTitle = truncatedTitle.substring(0, MAX_TITLE_LENGTH).trim();
        let lastSpaceIndex = tempTitle.lastIndexOf(" ");
        if (lastSpaceIndex !== -1) {
            truncatedTitle = tempTitle.substring(0, lastSpaceIndex) + '...';
        } else {
            truncatedTitle = tempTitle + '...';
        }
    } else if (truncatedTitle.length === 0) {
        truncatedTitle = 'Новый чат';
    }

    newHistoryItem.href = `/chat/${chatId}`;
    newHistoryItem.classList.add('history-item');
    newHistoryItem.textContent = truncatedTitle;
    newHistoryItem.dataset.chatId = chatId;

    // Добавляем в начало списка
    historyList.prepend(newHistoryItem);

    // Привязываем обработчик
    newHistoryItem.addEventListener('click', handleHistoryItemClick);

    return newHistoryItem;
}

/**
 * Обработчик нажатия на элемент истории.
 */
function handleHistoryItemClick(e) {
    e.preventDefault();
    const item = e.currentTarget;
    const chatId = parseInt(item.dataset.chatId);

    if (!isNaN(chatId)) {
        window.currentChatId = chatId;
    }

    // Очищаем историю
    chatHistoryContainer.innerHTML = '';
    hideTypingIndicator();

    // Обновляем заголовок
    document.querySelector('.chat-title').textContent = item.textContent;

    // Активируем режим чата
    activateChatMode();

    // Имитация загрузки истории
    createMessage('ai', 'Вы вернулись к старому чату.');
    createMessage('user', 'Проверка истории...');
}

/**
 * Переключает интерфейс в режим "Активный чат".
 */
function activateChatMode() {
    body.classList.add('chat-active');
    hideTypingIndicator();
}

/**
 * Переключает интерфейс в режим "Новый чат".
 */
function activateStartMode() {
    body.classList.remove('chat-active');

    // Очищаем историю сообщений
    chatHistoryContainer.innerHTML = '';

    // Сбрасываем поле ввода и файлы
    textarea.value = '';
    clearAttachedFiles();
    autoResizeTextarea();

    // Сбрасываем ID
    window.currentChatId = null;

    // Скрываем индикатор
    hideTypingIndicator();

    // Возвращаем стандартный заголовок
    document.querySelector('.chat-title').textContent = 'Новый чат';

    // Фокусируемся на поле ввода
    textarea.focus();
}

/**
 * Создание нового чата (симуляция API).
 */
async function createNewChat(initialMessage) {
    // Симуляция задержки сети
    await new Promise(resolve => setTimeout(resolve, 300));

    chatIdCounter++;
    const title = initialMessage.trim() || "Новый чат";

    return {
        chat_id: chatIdCounter,
        title: title
    };
}

/**
 * Основная функция отправки сообщения.
 */
async function sendMessage() {
    const messageText = textarea.value.trim();
    const filesToSend = [...attachedFiles];

    // Проверка на пустое сообщение
    if (messageText === '' && filesToSend.length === 0) {
        return;
    }

    // Отображаем сообщение пользователя
    createMessage('user', messageText);

    // Очищаем поле ввода
    textarea.value = '';
    clearAttachedFiles();
    autoResizeTextarea();

    // Фокусируемся обратно на поле ввода
    textarea.focus();

    // Показываем индикатор печати
    showTypingIndicator();

    try {
        // Если это новый чат
        if (window.currentChatId === null) {
            const newChatData = await createNewChat(messageText);
            window.currentChatId = newChatData.chat_id;

            // Добавляем в сайдбар
            createHistoryItem(newChatData.chat_id, newChatData.title);

            // Включаем режим чата
            activateChatMode();

            // Обновляем заголовок
            document.querySelector('.chat-title').textContent = newChatData.title;
        }

        // Имитация задержки ответа от сервера
        await new Promise(resolve => setTimeout(resolve, 1500));

        // Скрываем индикатор печати
        hideTypingIndicator();

        // Создаем имитацию ответа AI
        let response = `Это ответ AI на сообщение: "${messageText}". `;
        if (filesToSend.length > 0) {
            const fileNames = filesToSend.map(f => f.name).join(', ');
            response += `Были прикреплены файлы: ${fileNames}.`;
        } else {
            response += `Файлы не прикреплены.`;
        }

        // Отображаем ответ AI
        createMessage('ai', response);

    } catch (error) {
        console.error('Ошибка:', error);
        hideTypingIndicator();
        createMessage('ai', 'Извините, произошла ошибка. Пожалуйста, попробуйте еще раз.');
    }
}

// 3. ПРИВЯЗКА СОБЫТИЙ И ИНИЦИАЛИЗАЦИЯ

// Автоматический ресайз при вводе
textarea.addEventListener('input', autoResizeTextarea);

// Отправка сообщения по клавише Enter
textarea.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// Отправка сообщения по кнопке
sendButton.addEventListener('click', sendMessage);

// Кнопка "Новый чат"
newChatButton.addEventListener('click', (e) => {
    e.preventDefault();
    activateStartMode();
});

// Кнопка прикрепления файлов
attachButton.addEventListener('click', () => {
    fileInput.click();
});

// Обработка выбора файлов
fileInput.addEventListener('change', () => {
    Array.from(fileInput.files).forEach(file => {
        // Проверка на дубликаты
        if (!attachedFiles.some(f => f.name === file.name && f.size === file.size)) {
            attachedFiles.push(file);
        }
    });
    renderFileChips();
});

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    console.log('Приложение инициализировано');

    autoResizeTextarea();
    hideTypingIndicator();
    activateStartMode();

    // Фокусируемся на поле ввода
    textarea.focus();
});