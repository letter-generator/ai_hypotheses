from flask import Flask, request, jsonify, session
from flask_cors import CORS
import uuid
from models import db, User, ChatSession, Message

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chatbot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_TYPE'] = 'filesystem'

# Инициализация БД
db.init_app(app)

# CORS для связи с фронтендом
CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:5500"], supports_credentials=True)

# Создание таблиц
with app.app_context():
    db.create_all()

# Генерация/получение ID пользователя
def get_or_create_user():
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        user_id = str(uuid.uuid4())
    
    # Проверяем существование пользователя в БД
    user = User.query.get(user_id)
    if not user:
        user = User(id=user_id)
        db.session.add(user)
        db.session.commit()
    
    return user_id

@app.route('/api/new_chat', methods=['POST'])
def new_chat():
    try:
        user_id = get_or_create_user()
        data = request.json
        
        # Создаем новую сессию чата
        title = data.get('title', 'Новый чат')
        new_chat = ChatSession(user_id=user_id, title=title)
        db.session.add(new_chat)
        db.session.commit()
        
        return jsonify({
            'chat_id': new_chat.id,
            'title': new_chat.title
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/send_message', methods=['POST'])
def send_message():
    try:
        user_id = get_or_create_user()
        data = request.json
        
        chat_id = data.get('chat_id')
        message = data.get('message')
        attachments = data.get('attachments', [])
        
        if not chat_id or not message:
            return jsonify({'error': 'Missing chat_id or message'}), 400
        
        # Проверяем существование чата
        chat = ChatSession.query.filter_by(id=chat_id, user_id=user_id).first()
        if not chat:
            return jsonify({'error': 'Chat not found or access denied'}), 404
        
        # Сохраняем сообщение пользователя
        user_message = Message(
            chat_id=chat_id, 
            content=message, 
            is_user=True,
            attachments=str(attachments) if attachments else None
        )
        db.session.add(user_message)
        
        # Обновляем заголовок чата (если это первое сообщение)
        if len(chat.messages) == 0:
            chat.title = message[:50] + "..." if len(message) > 50 else message
            db.session.add(chat)
        
        db.session.flush()  # Получаем ID сообщения
        
        # Генерируем ответ бота (заглушка, позже подключите RAG)
        bot_response = f"Это ответ AI на сообщение: '{message}'"
        if attachments:
            file_names = ', '.join([att.get('name', '') for att in attachments])
            bot_response += f"\nПрикреплённые файлы: {file_names}"
        
        # Сохраняем ответ бота
        bot_message = Message(
            chat_id=chat_id, 
            content=bot_response, 
            is_user=False
        )
        db.session.add(bot_message)
        
        db.session.commit()
        
        return jsonify({
            'user_message': {
                'id': user_message.id,
                'content': message,
                'is_user': True,
                'created_at': user_message.created_at.isoformat(),
                'attachments': attachments
            },
            'bot_response': {
                'id': bot_message.id,
                'content': bot_response,
                'is_user': False,
                'created_at': bot_message.created_at.isoformat()
            },
            'chat_id': chat_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat_history', methods=['GET'])
def get_chat_history():
    try:
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify([])
        
        # Получаем все чаты пользователя
        chats = ChatSession.query.filter_by(user_id=user_id).order_by(ChatSession.created_at.desc()).all()
        
        chat_list = []
        for chat in chats:
            # Получаем последнее сообщение для превью
            last_message = Message.query.filter_by(chat_id=chat.id).order_by(Message.created_at.desc()).first()
            
            chat_list.append({
                'chat_id': chat.id,
                'title': chat.title,
                'created_at': chat.created_at.isoformat(),
                'last_message': last_message.content if last_message else None,
                'last_message_time': last_message.created_at.isoformat() if last_message else None
            })
        
        return jsonify(chat_list), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/<int:chat_id>/messages', methods=['GET'])
def get_chat_messages(chat_id):
    try:
        user_id = request.headers.get('X-User-ID')
        
        # Проверяем доступ к чату
        chat = ChatSession.query.filter_by(id=chat_id, user_id=user_id).first()
        if not chat:
            return jsonify({'error': 'Chat not found or access denied'}), 404
        
        # Получаем все сообщения конкретного чата
        messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.created_at).all()
        
        message_list = []
        for msg in messages:
            message_list.append({
                'id': msg.id,
                'text': msg.content,
                'sender': 'user' if msg.is_user else 'ai',
                'ts': msg.created_at.timestamp() * 1000,
                'attachments': eval(msg.attachments) if msg.attachments else []
            })
        
        return jsonify({
            'chat_id': chat_id,
            'title': chat.title,
            'messages': message_list
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)