// Получаем элемент поля ввода
const textarea = document.querySelector('.chat-textarea');
const MAX_HEIGHT = 200;

// Функция, которая корректирует высоту
function autoResizeTextarea() {
    textarea.style.height = 'auto'; // Сначала сбрасываем высоту, чтобы узнать фактическую высоту содержимого
    const newHeight = Math.min(textarea.scrollHeight, MAX_HEIGHT); // Вычисляем новую высоту: либо высота содержимого, либо MAX_HEIGHT
    textarea.style.height = newHeight + 'px'; // Применяем новую высоту
}

textarea.addEventListener('input', autoResizeTextarea); // Привязываем функцию к событию ввода

autoResizeTextarea(); // Вызываем один раз при загрузке, на случай если там уже есть текст

// Получаем контейнер истории чата
const chatHistoryContainer = document.querySelector('.chat-history-container');

// Функция, которая прокручивает историю вниз
function scrollToBottom() {
    chatHistoryContainer.scrollTop = chatHistoryContainer.scrollHeight; // Используем свойство scrollHeight для прокрутки к самому низу
}

scrollToBottom(); // 6. Вызываем прокрутку при запуске, чтобы показать последние сообщения

// Получаем необходимые элементы DOM
const body = document.body;
const sendButton = document.querySelector('.send-button');
const newChatButton = document.querySelector('.nav-button[href="/new-chat"]');
const historyItems = document.querySelectorAll('.history-item');

// Функция переключения в режим "Активный чат"
function activateChatMode() {
    body.classList.add('chat-active');// Добавляем класс, который меняет макет
    textarea.value = ''; // Очищаем поле ввода
    autoResizeTextarea(); // Сбрасываем высоту поля ввода
    scrollToBottom(); // Прокручиваем к последнему сообщению (если оно есть)
}

// Функция переключения в режим "Стартовый экран" (Новый чат)
function activateStartMode() {
    body.classList.remove('chat-active'); // Удаляем класс, возвращая макет к центрированному полю ввода
    textarea.value = '';
    autoResizeTextarea();
}

// Привязка событий

// При нажатии на кнопку "Отправить"
sendButton.addEventListener('click', () => {
    if (textarea.value.trim() !== '') {
        // Здесь в будущем будет логика отправки на бэкенд
        // Пока просто активируем режим чата и очищаем поле
        activateChatMode();
    }
});

// При нажатии на кнопку "Новый чат"
newChatButton.addEventListener('click', (e) => {
    e.preventDefault(); // Отменяем стандартный переход по ссылке
    activateStartMode();
});

// При нажатии на элементы истории (для демонстрации)
historyItems.forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();
        activateChatMode(); // Переключаемся в режим чата с историей
    });
});