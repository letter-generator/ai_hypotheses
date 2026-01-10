from flask import Flask, request, jsonify, session
from flask_cors import CORS
import uuid
from models import db, User, ChatSession, Message, Review

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
    if not user_id:
        user_id = str(uuid.uuid4())
    
    user = User.query.get(user_id)
    if not user:
        user = User(id=user_id)
        db.session.add(user)
        db.session.commit()
    
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
        
        chat = ChatSession.query.filter_by(id=chat_id, user_id=user_id).first()
        if not chat:
            return jsonify({'error': 'Chat not found or access denied'}), 404
        
        user_message = Message(
            chat_id=chat_id, 
            content=message, 
            is_user=True,
            attachments=str(attachments) if attachments else None
        )
        db.session.add(user_message)
        
        if len(chat.messages) == 0:
            chat.title = message[:50] + "..." if len(message) > 50 else message
            db.session.add(chat)
        
        db.session.flush()
        
        bot_response = f"Это ответ AI на сообщение: '{message}'"
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
        
        return jsonify(chat_list), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/<int:chat_id>/messages', methods=['GET'])
def get_chat_messages(chat_id):
    try:
        user_id = request.headers.get('X-User-ID')
        chat = ChatSession.query.filter_by(id=chat_id, user_id=user_id).first()
        if not chat:
            return jsonify({'error': 'Chat not found or access denied'}), 404
        
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