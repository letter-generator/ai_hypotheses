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
