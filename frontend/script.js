// Основные элементы
const body = document.body;
const textarea = document.querySelector('.chat-textarea');
const chatHistoryContainer = document.querySelector('.chat-history-container');
const MAX_HEIGHT = 200;

// Кнопки и навигация
const sendButton = document.querySelector('.send-button');
const attachButton = document.querySelector('.attach-button');
const newChatButton = document.querySelector('.nav-button[href="/new-chat"]');
const historyItems = document.querySelectorAll('.history-item');

// Логика прикрепления файлов
const fileInput = document.getElementById('file-input');
const fileChipContainer = document.querySelector('.file-chip-container');
// Массив для хранения выбранных файлов
let attachedFiles = [];

// Автоматический ресайз)
function autoResizeTextarea() {
    textarea.style.height = 'auto';
    const newHeight = Math.min(textarea.scrollHeight, MAX_HEIGHT);
    textarea.style.height = newHeight + 'px';
}

// Функция, которая прокручивает историю вниз
function scrollToBottom() {
    chatHistoryContainer.scrollTop = chatHistoryContainer.scrollHeight;
}

// Функция для отрисовки всех чипов на основе массива attachedFiles
function renderFileChips() {
    fileChipContainer.innerHTML = ''; // Очищаем контейнер

    if (attachedFiles.length === 0) {
        fileChipContainer.style.display = 'none';
        return;
    }

    attachedFiles.forEach((file, index) => {
        // Создаем HTML для чипа, используя index для идентификации при удалении
        const chipHTML = `
            <div class="file-chip">
                <span class="file-chip-text" title="${file.name}">${file.name}</span>
                <button class="file-chip-delete" data-file-index="${index}">×</button>
            </div>
        `;
        fileChipContainer.innerHTML += chipHTML;
    });

    fileChipContainer.style.display = 'flex';

    // Привязываем слушатели к кнопкам удаления после добавления всех чипов
    fileChipContainer.querySelectorAll('.file-chip-delete').forEach(button => {
        button.addEventListener('click', removeFileChip);
    });
}

// Функция для удаления чипа
function removeFileChip(e) {
    if (e && e.target.classList.contains('file-chip-delete')) {
        const indexToRemove = parseInt(e.target.getAttribute('data-file-index')); // Получаем индекс файла, который нужно удалить
        attachedFiles.splice(indexToRemove, 1); // Удаляем файл из массива attachedFiles
        renderFileChips(); // Перерисовываем контейнер, чтобы обновить чипы и индексы

    } else {
        // Логика, которая вызывается, когда нужно скрыть все (например, при Новом чате)
        attachedFiles = []; // Очищаем массив
        fileInput.value = '';
        renderFileChips(); // Скрывает контейнер
    }
}

// Функция переключения в режим "Активный чат"
function activateChatMode() {
    body.classList.add('chat-active');
    textarea.value = '';
    removeFileChip(); // Используем функцию для полного сброса чипов и массива attachedFiles
    autoResizeTextarea();
    scrollToBottom();
}

// Функция переключения в режим "Новый чат"
function activateStartMode() {
    body.classList.remove('chat-active');
    textarea.value = '';
    attachedFiles = []; // Очищаем прикрепленные файлы
    renderFileChips(); // Скрываем чипы
    autoResizeTextarea();
}

// Автоматический ресайз при вводе
textarea.addEventListener('input', autoResizeTextarea);

// Отправка сообщения по клавише Enter
textarea.addEventListener('keydown', (e) => {
    // Проверяем Enter без Shift
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (textarea.value.trim() !== '' || attachedFiles.length > 0) {
            // Отправляем, если есть текст ИЛИ прикреплены файлы
            activateChatMode();
        }
    }
});

// Отправка сообщения по кнопке "Отправить"
sendButton.addEventListener('click', () => {
    if (textarea.value.trim() !== '' || attachedFiles.length > 0) {
        activateChatMode();
    }
});

// Кнопка "Новый чат"
newChatButton.addEventListener('click', (e) => {
    e.preventDefault();
    activateStartMode();
});

// Элементы истории (Переключают в режим чата)
historyItems.forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();
        activateChatMode();
    });
});

// Логика кнопки-скрепки
attachButton.addEventListener('click', () => {
    fileInput.click(); // Кликаем по скрытому полю ввода
});

// Обработка выбора файла
fileInput.addEventListener('change', () => {
    // Добавляем новые выбранные файлы к общему списку
    Array.from(fileInput.files).forEach(file => {
        attachedFiles.push(file);
    });
    // Перерисовываем чипы
    renderFileChips();
    // Сбрасываем значение input[type="file"], чтобы можно было выбрать те же файлы снова
    fileInput.value = '';
});

// Инициализация
autoResizeTextarea();
scrollToBottom();
renderFileChips(); // Проверяем, если нужно что-то отобразить при загрузке