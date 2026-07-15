from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

# 1. جدول المستخدمين (حماية كاملة بكلمات مرور مشفرة)
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # علاقات لربط المستخدم بالقصص والتعليقات والرسائل
    stories = db.relationship('Story', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)

    # دالة لتشفير كلمة المرور قبل حفظها
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # دالة للتحقق من كلمة المرور عند تسجيل الدخول
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# 2. جدول القصص
class Story(db.Model):
    __tablename__ = 'stories'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    challenge = db.Column(db.Text, nullable=False)
    turning_point = db.Column(db.Text, nullable=False)
    outcome = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    comments = db.relationship('Comment', backref='story', lazy=True, cascade="all, delete-orphan")

# 3. جدول التعليقات (مع حماية برمجية لربطها بالقصة وصاحبها)
class Comment(db.Model):
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('stories.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 4. جدول الرسائل الخاصة والمباشرة (DMs) بين المستخدمين
class DirectMessage(db.Model):
    __tablename__ = 'direct_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message_text = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # تعريف العلاقات البرمجية للمرسل والمستقبل
    sender = db.relationship('User', foreign_keys=[sender_id], backref=db.backref('sent_messages', lazy=True))
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref=db.backref('received_messages', lazy=True))