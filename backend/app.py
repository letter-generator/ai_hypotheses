from flask import Flask, request, jsonify, session
from flask_cors import CORS
import uuid
from models import db, User, ChatSession, Message

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chatbot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация БД
db.init_app(app)

# CORS для связи с фронтендом
CORS(app)

# Создание таблиц
with app.app_context():
    db.create_all()

# Генерация/получение ID пользователя
def get_user_id():
    if 'user_id' not in session:
        user_id = str(uuid.uuid4())
        session['user_id'] = user_id
        
        # Создаем нового пользователя в БД
        new_user = User(id=user_id)
        db.session.add(new_user)
        db.session.commit()
    
    return session['user_id']

@app.route('/api/new_chat', methods=['GET','POST'])
def new_chat():
    user_id = get_user_id()
    
    # Создаем новую сессию чата
    new_chat = ChatSession(user_id=user_id, title="Новый чат")
    db.session.add(new_chat)
    db.session.commit()
    
    return jsonify({
        'chat_id': new_chat.id,
        'title': new_chat.title
    })

@app.route('/api/send_message', methods=['GET','POST'])
def send_message():
    # Если GET запрос - показываем форму для тестирования
    if request.method == 'GET':
        return '''
        <h3>Тест отправки сообщения</h3>
        <form method="POST">
            Chat ID: <input type="number" name="chat_id" value="1"><br>
            Message: <input type="text" name="message" value="Тестовое сообщение"><br>
            <input type="submit" value="Отправить">
        </form>
        '''
    
    # Обрабатываем оба типа Content-Type
    if request.content_type == 'application/json':
        data = request.json
    else:
        data = request.form
    
    chat_id = data.get('chat_id')
    message = data.get('message')
    
    # Проверяем обязательные поля
    if not chat_id or not message:
        return jsonify({'error': 'Missing chat_id or message'}), 400
    
    # Преобразуем chat_id в число
    try:
        chat_id = int(chat_id)
    except (TypeError, ValueError):
        return jsonify({'error': 'chat_id must be a number'}), 400
    
    # Сохраняем сообщение пользователя
    user_message = Message(chat_id=chat_id, content=message, is_user=True)
    db.session.add(user_message)
    
    # Здесь вызывайте вашу RAG логику из rag_prototype.py
    # bot_response = rag_prototype.get_response(message)
    bot_response = f"Это ответ бота на: '{message}'"  # заглушка
    
    # Сохраняем ответ бота
    bot_message = Message(chat_id=chat_id, content=bot_response, is_user=False)
    db.session.add(bot_message)
    
    # Обновляем заголовок чата (если это первое сообщение)
    chat = ChatSession.query.get(chat_id)
    if chat and len(chat.messages) == 0:  # проверяем ДО добавления сообщений
        chat.title = message[:50] + "..." if len(message) > 50 else message
        db.session.add(chat)
    
    db.session.commit()
    
    return jsonify({
        'user_message': message,
        'bot_response': bot_response,
        'chat_id': chat_id
    })

@app.route('/api/chat_history', methods=['GET'])
def get_chat_history():
    user_id = get_user_id()
    
    # Получаем все чаты пользователя
    chats = ChatSession.query.filter_by(user_id=user_id).order_by(ChatSession.created_at.desc()).all()
    
    chat_list = []
    for chat in chats:
        chat_list.append({
            'id': chat.id,
            'title': chat.title,
            'created_at': chat.created_at.isoformat()
        })
    
    return jsonify(chat_list)

@app.route('/api/chat/<int:chat_id>', methods=['GET'])
def get_chat_messages(chat_id):
    # Получаем все сообщения конкретного чата
    chat = ChatSession.query.get_or_404(chat_id)
    messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.created_at).all()
    
    message_list = []
    for msg in messages:
        message_list.append({
            'id': msg.id,
            'content': msg.content,
            'is_user': msg.is_user,
            'created_at': msg.created_at.isoformat()
        })
    
    return jsonify(message_list)

if __name__ == '__main__':
    app.run(debug=True)