from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.String(36), primary_key=True)  # уникальный ID пользователя
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ChatSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'))
    title = db.Column(db.String(200))  # начало первого сообщения как заголовок
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связь с пользователем
    user = db.relationship('User', backref=db.backref('chats', lazy=True))

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat_session.id'))
    content = db.Column(db.Text)
    is_user = db.Column(db.Boolean)  # True - сообщение от пользователя, False - от бота
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связь с чатом
    chat = db.relationship('ChatSession', backref=db.backref('messages', lazy=True))