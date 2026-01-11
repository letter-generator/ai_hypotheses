from flask import Flask, request, jsonify, session
from flask_cors import CORS
import uuid
import sys
import os
from models import db, User, ChatSession, Message, Review

sys.path.append(os.path.join(os.path.dirname(__file__)))

try:
    from rag import ask, generate_hypotheses
    RAG_AVAILABLE = True
    print("RAG система загружена")
except ImportError as e:
    print(f"Warning: RAG module not available: {e}")
    print("Using dummy responses instead.")
    RAG_AVAILABLE = False
except Exception as e:
    print(f"Warning: Error importing RAG module: {e}")
    RAG_AVAILABLE = False

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chatbot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_TYPE'] = 'filesystem'

db.init_app(app)
CORS(app, origins=["http://localhost:5500", "http://127.0.0.1:5500", "http://localhost:3000", "http://127.0.0.1:3000"], supports_credentials=True)

with app.app_context():
    db.create_all()

def get_or_create_user():
    user_id = request.headers.get('X-User-ID')
    print(f"Получен X-User-ID из заголовков: {user_id}")
    
    if not user_id:
        user_id = str(uuid.uuid4())
        print(f"Создан новый user_id: {user_id}")
    
    user = User.query.get(user_id)
    if not user:
        user = User(id=user_id)
        db.session.add(user)
        db.session.commit()
        print(f"Создан новый пользователь в БД: {user_id}")
    
    return user_id

@app.route('/api/reviews', methods=['POST'])
def add_review():
    try:
        user_id = get_or_create_user()
        data = request.json
        rating = data.get('rating')
        text = data.get('text')
        
        if not rating or not text:
            return jsonify({'error': 'Missing rating or text'}), 400
        
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            return jsonify({'error': 'Rating must be integer between 1 and 5'}), 400
        
        new_review = Review(
            user_id=user_id,
            rating=rating,
            text=text.strip()
        )
        
        db.session.add(new_review)
        db.session.commit()
        
        return jsonify({
            'id': new_review.id,
            'user_id': new_review.user_id,
            'rating': new_review.rating,
            'text': new_review.text,
            'created_at': new_review.created_at.isoformat()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/reviews', methods=['GET'])
def get_reviews():
    try:
        reviews = Review.query.order_by(Review.created_at.desc()).all()
        reviews_list = []
        for review in reviews:
            reviews_list.append({
                'id': review.id,
                'user_id': review.user_id,
                'rating': review.rating,
                'text': review.text,
                'created_at': review.created_at.isoformat()
            })
        
        return jsonify(reviews_list), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reviews/stats', methods=['GET'])
def get_review_stats():
    try:
        total_reviews = Review.query.count()
        
        if total_reviews == 0:
            return jsonify({
                'average_rating': 0,
                'total_reviews': 0,
                'distribution': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            }), 200
        
        avg_result = db.session.query(db.func.avg(Review.rating)).scalar()
        average_rating = round(float(avg_result), 1) if avg_result else 0
        
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for i in range(1, 6):
            count = Review.query.filter_by(rating=i).count()
            distribution[i] = count
        
        return jsonify({
            'average_rating': average_rating,
            'total_reviews': total_reviews,
            'distribution': distribution
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reviews/<int:review_id>', methods=['DELETE'])
def delete_review(review_id):
    try:
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({'error': 'User ID required'}), 401
        
        review = Review.query.get(review_id)
        if not review:
            return jsonify({'error': 'Review not found'}), 404
        
        if review.user_id != user_id:
            return jsonify({'error': 'Cannot delete other user\'s review'}), 403
        
        db.session.delete(review)
        db.session.commit()
        
        return jsonify({'message': 'Review deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/new_chat', methods=['POST'])
def new_chat():
    try:
        user_id = get_or_create_user()
        data = request.json
        
        title = data.get('title', 'Новый чат')
        new_chat = ChatSession(user_id=user_id, title=title)
        db.session.add(new_chat)
        db.session.commit()
        
        print(f"Создан новый чат: ID={new_chat.id}, user_id={user_id}, title={title}")
        
        return jsonify({
            'chat_id': new_chat.id,
            'title': new_chat.title
        }), 200
    except Exception as e:
        print(f"Ошибка создания чата: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/send_message', methods=['POST'])
def send_message():
    try:
        user_id = get_or_create_user()
        data = request.json
        
        chat_id = data.get('chat_id')
        message = data.get('message')
        attachments = data.get('attachments', [])
        
        print(f"Получено сообщение: chat_id={chat_id}, user_id={user_id}, message={message[:50]}...")
        
        if not chat_id or not message:
            return jsonify({'error': 'Missing chat_id or message'}), 400
        
        chat = ChatSession.query.filter_by(id=chat_id, user_id=user_id).first()
        if not chat:
            print(f"Чат не найден: chat_id={chat_id}, user_id={user_id}")
            return jsonify({'error': 'Chat not found or access denied'}), 404
        
        print(f"Чат найден: {chat.title}")
        
        user_message = Message(
            chat_id=chat_id, 
            content=message, 
            is_user=True,
            attachments=str(attachments) if attachments else None
        )
        db.session.add(user_message)
        
        # ОБНОВЛЯЕМ ЗАГОЛОВОК ЧАТА ТОЛЬКО КОГДА ЭТО ПЕРВОЕ СООБЩЕНИЕ С ВЫБОРОМ РЕЖИМА
        if len(chat.messages) == 0:
            # Для первого сообщения оставляем заголовок "Новый чат"
            chat.title = "Новый чат"
            db.session.add(chat)
            print(f"Установлен заголовок чата: {chat.title}")
        
        db.session.flush()
        
        bot_response = ""
        mode = None
        
        try:
            # Проверяем, нужно ли определять режим работы
            if len(chat.messages) == 1:  # Это первое сообщение пользователя
                message_lower = message.lower().strip()
                
                if 'вопрос' in message_lower:
                    mode = 'question'
                    bot_response = "Отлично! Вы выбрали режим **вопросов**. Теперь я буду отвечать на ваши вопросы на основе доступных знаний.\n\nЧто вы хотите узнать?"
                
                elif 'гипотез' in message_lower or 'генер' in message_lower:
                    mode = 'hypothesis'
                    bot_response = "Отлично! Вы выбрали режим **генерации гипотез**. Я буду анализировать проблему и предлагать научно обоснованные гипотезы.\n\nОпишите проблему или тему, по которой вы хотите сгенерировать гипотезы:"
                
                else:
                    mode = 'choice'
                    bot_response = "Вы хотите задать **вопрос** или сгенерировать **гипотезу**?\n\nПожалуйста, ответьте:\n- 'вопрос' - для получения ответов на вопросы\n- 'гипотеза' - для генерации научных гипотез"
            
            else:
                # Определяем режим на основе истории чата
                # Ищем первое сообщение пользователя, чтобы определить режим
                first_user_msg = Message.query.filter_by(
                    chat_id=chat_id, 
                    is_user=True
                ).order_by(Message.created_at.asc()).first()
                
                if first_user_msg:
                    first_msg_lower = first_user_msg.content.lower().strip()
                    if 'вопрос' in first_msg_lower:
                        mode = 'question'
                    elif 'гипотез' in first_msg_lower or 'генер' in first_msg_lower:
                        mode = 'hypothesis'
                    else:
                        # Если первое сообщение не выбор режима, то это второе сообщение (вопрос/проблема)
                        # ОБНОВЛЯЕМ ЗАГОЛОВОК ЧАТА НА ОСНОВЕ ЭТОГО СООБЩЕНИЯ
                        if chat.title == "Новый чат":
                            # Обрезаем слишком длинные сообщения для заголовка
                            title_text = first_msg_lower[:100]
                            if len(first_msg_lower) > 100:
                                title_text += "..."
                            chat.title = title_text.capitalize()
                            db.session.add(chat)
                            print(f"Обновлен заголовок чата на основе вопроса: {chat.title}")
                
                # Если режим определен, обрабатываем запрос
                if mode == 'question' and RAG_AVAILABLE:
                    print(f"Обработка вопроса: {message[:100]}...")
                    bot_response = ask(message)
                    print(f"Получен ответ от RAG ({len(bot_response)} символов)")
                    
                    # ОБНОВЛЯЕМ ЗАГОЛОВОК ДЛЯ РЕЖИМА ВОПРОСОВ
                    if chat.title == "Новый чат":
                        title_text = message[:100]
                        if len(message) > 100:
                            title_text += "..."
                        chat.title = title_text.capitalize()
                        db.session.add(chat)
                        print(f"Обновлен заголовок чата для вопроса: {chat.title}")
                
                elif mode == 'hypothesis' and RAG_AVAILABLE:
                    print(f"Генерация гипотез для: {message[:100]}...")
                    try:
                        final_hypotheses, raw_hypotheses, docs = generate_hypotheses(message)
                        
                        # Форматируем ответ
                        bot_response = f"## Сгенерированные гипотезы\n\n"
                        bot_response += f"**Проблема:** {message}\n\n"
                        bot_response += f"**На основе источников:**\n"
                        for i, doc in enumerate(docs[:3], 1):
                            bot_response += f"{i}. {doc.metadata.get('title', 'Без названия')}\n"
                        bot_response += f"\n**Гипотезы:**\n\n{final_hypotheses}"
                        
                        print(f"Сгенерировано гипотез: {len(final_hypotheses)} символов")
                        
                        # ОБНОВЛЯЕМ ЗАГОЛОВОК ДЛЯ РЕЖИМА ГИПОТЕЗ
                        if chat.title == "Новый чат":
                            title_text = message[:100]
                            if len(message) > 100:
                                title_text += "..."
                            chat.title = title_text.capitalize()
                            db.session.add(chat)
                            print(f"Обновлен заголовок чата для гипотезы: {chat.title}")
                        
                    except Exception as hyp_error:
                        print(f"Ошибка генерации гипотез: {hyp_error}")
                        bot_response = f"Извините, произошла ошибка при генерации гипотез. Попробуйте ещё раз."
                
                elif not RAG_AVAILABLE:
                    bot_response = f"Это ответ AI на сообщение: '{message}'"
                    print("RAG недоступен, использую фиктивный ответ")
                    
                    # ОБНОВЛЯЕМ ЗАГОЛОВОК ДЛЯ ФИКТИВНЫХ ОТВЕТОВ
                    if chat.title == "Новый чат":
                        title_text = message[:100]
                        if len(message) > 100:
                            title_text += "..."
                        chat.title = title_text.capitalize()
                        db.session.add(chat)
                        print(f"Обновлен заголовок чата для фиктивного ответа: {chat.title}")
                
                else:
                    bot_response = "Пожалуйста, сначала выберите режим работы. Напишите 'вопрос' или 'гипотеза'."
            
            if attachments:
                file_names = ', '.join([att.get('name', '') for att in attachments])
                bot_response = f"{bot_response}\n\n Прикреплённые файлы: {file_names}"
                
        except Exception as rag_error:
            print(f"Ошибка RAG: {rag_error}")
            bot_response = f"Извините, произошла ошибка при обработке запроса. Пожалуйста, попробуйте ещё раз."
            if attachments:
                file_names = ', '.join([att.get('name', '') for att in attachments])
                bot_response += f"\nПрикреплённые файлы: {file_names}"
        
        bot_message = Message(
            chat_id=chat_id, 
            content=bot_response, 
            is_user=False
        )
        db.session.add(bot_message)
        
        db.session.commit()
        
        print(f"Сообщение сохранено в БД: user_msg_id={user_message.id}, bot_msg_id={bot_message.id}, mode={mode}, chat_title={chat.title}")
        
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
            'chat_id': chat_id,
            'mode': mode,
            'chat_title': chat.title  # Добавляем обновленный заголовок в ответ
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Общая ошибка в send_message: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat_history', methods=['GET'])
def get_chat_history():
    try:
        user_id = request.headers.get('X-User-ID')
        print(f"Получение истории чатов для user_id: {user_id}")
        
        if not user_id:
            print("user_id не указан, возвращаем пустой список")
            return jsonify([]), 200
        
        chats = ChatSession.query.filter_by(user_id=user_id).order_by(ChatSession.created_at.desc()).all()
        chat_list = []
        for chat in chats:
            last_message = Message.query.filter_by(chat_id=chat.id).order_by(Message.created_at.desc()).first()
            chat_list.append({
                'chat_id': chat.id,
                'title': chat.title,
                'created_at': chat.created_at.isoformat(),
                'last_message': last_message.content if last_message else None,
                'last_message_time': last_message.created_at.isoformat() if last_message else None
            })
        
        print(f"Найдено {len(chat_list)} чатов для пользователя {user_id}")
        return jsonify(chat_list), 200
    except Exception as e:
        print(f"Ошибка получения истории: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/<int:chat_id>/messages', methods=['GET'])
def get_chat_messages(chat_id):
    try:
        user_id = request.headers.get('X-User-ID')
        print(f"Получение сообщений чата: chat_id={chat_id}, user_id={user_id}")
        
        if not user_id:
            print("user_id не указан в заголовках")
            return jsonify({'error': 'User ID required in X-User-ID header'}), 401
        
        chat = ChatSession.query.filter_by(id=chat_id, user_id=user_id).first()
        if not chat:
            print(f"Чат не найден или доступ запрещен: chat_id={chat_id}, user_id={user_id}")
            
            user_chats = ChatSession.query.filter_by(user_id=user_id).all()
            print(f"Чаты пользователя {user_id}: {[c.id for c in user_chats]}")
            
            return jsonify({'error': 'Chat not found or access denied'}), 404
        
        messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.created_at).all()
        message_list = []
        for msg in messages:
            try:
                attachments = eval(msg.attachments) if msg.attachments else []
            except:
                attachments = []
                
            message_list.append({
                'id': msg.id,
                'text': msg.content,
                'sender': 'user' if msg.is_user else 'ai',
                'ts': msg.created_at.timestamp() * 1000,
                'attachments': attachments
            })
        
        print(f"Найдено {len(message_list)} сообщений в чате {chat_id}")
        
        return jsonify({
            'chat_id': chat_id,
            'title': chat.title,
            'messages': message_list
        }), 200
    
    except Exception as e:
        print(f"Ошибка получения сообщений чата: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/rag_status', methods=['GET'])
def get_rag_status():
    """Проверка статуса RAG-системы"""
    return jsonify({
        'rag_available': RAG_AVAILABLE,
        'status': 'ready' if RAG_AVAILABLE else 'not_available'
    }), 200

@app.route('/api/test_rag', methods=['POST'])
def test_rag():
    """Тестовый endpoint для проверки RAG"""
    try:
        if not RAG_AVAILABLE:
            return jsonify({'error': 'RAG not available'}), 503
        
        data = request.json
        test_message = data.get('message', 'Привет')
        
        try:
            response = ask(test_message)
            return jsonify({
                'success': True,
                'test_message': test_message,
                'response': response[:500]
            }), 200
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/debug/user', methods=['GET'])
def debug_user():
    """Отладочный endpoint для проверки пользователя"""
    user_id = get_or_create_user()
    chats = ChatSession.query.filter_by(user_id=user_id).all()
    
    return jsonify({
        'user_id': user_id,
        'chats': [{'id': c.id, 'title': c.title} for c in chats]
    }), 200

@app.route('/api/debug/chats', methods=['GET'])
def debug_chats():
    """Отладочный endpoint для всех чатов"""
    all_chats = ChatSession.query.all()
    
    return jsonify({
        'total_chats': len(all_chats),
        'chats': [{'id': c.id, 'user_id': c.user_id, 'title': c.title} for c in all_chats]
    }), 200

@app.route('/health', methods=['GET'])
def health_check():
    """Проверка работоспособности сервера"""
    return jsonify({
        'status': 'ok',
        'rag_available': RAG_AVAILABLE,
        'database': 'connected'
    }), 200

if __name__ == '__main__':
    print("=" * 50)
    print("Запуск Flask приложения с RAG-ботом")
    print(f"RAG доступен: {RAG_AVAILABLE}")
    print("=" * 50)
    
    if RAG_AVAILABLE:
        print("RAG система готова к работе")
    else:
        print("RAG система не доступна, будут использоваться фиктивные ответы")
    
    app.run(debug=True, port=5000)