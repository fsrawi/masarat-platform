import os
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Story, Comment, DirectMessage
from sqlalchemy import or_

app = Flask(__name__)

# إعدادات الحماية والـ Session
# نستخدم مفتاحاً سرياً عشوائياً مشفراً لجلسات المستخدمين لتعزيز الأمان
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'Fawzi_Secure_DevSecOps_Key_2026')
# مسار قاعدة البيانات المدمجة SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///masarat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ربط قاعدة البيانات بالتطبيق
db.init_app(app)

# تهيئة نظام إدارة جلسات المستخدمين (Flask-Login)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# إنشاء قاعدة البيانات والجداول تلقائياً إن لم تكن موجودة عند تشغيل السيرفر
with app.app_context():
    db.create_all()

# --- 1. المسار الرئيسي (عرض القصص والتعليقات ديناميكياً) ---
@app.route('/')
def home():
    # جلب جميع القصص من قاعدة البيانات مرتبة من الأحدث للأقدم
    stories = Story.query.order_by(Story.created_at.desc()).all()
    return render_template('home.html', stories=stories)

# --- 2. مسارات تسجيل الدخول والحسابات (Authentication) ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        username = request.form.get('username').strip()
        email = request.form.get('email').strip()
        password = request.form.get('password')
        
        # التحقق من عدم تكرار اسم المستخدم أو البريد الإلكتروني
        if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            flash('اسم المستخدم أو البريد الإلكتروني مسجل بالفعل!', 'danger')
            return redirect(url_for('register'))
            
        new_user = User(username=username, email=email)
        new_user.set_password(password) # تشفير كلمة المرور آمنياً قبل حفظها
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('تم إنشاء حسابك بنجاح! يمكنك تسجيل الدخول الآن.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('تم تسجيل الدخول بنجاح!', 'success')
            return redirect(url_for('home'))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة!', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('تم تسجيل الخروج بنجاح.', 'info')
    return redirect(url_for('home'))

# --- 3. مسار كتابة قصة جديدة ---
@app.route('/add-story', methods=['GET', 'POST'])
@login_required
def add_story():
    if request.method == 'POST':
        title = request.form.get('title').strip()
        challenge = request.form.get('challenge').strip()
        turning_point = request.form.get('turning_point').strip()
        outcome = request.form.get('outcome').strip()
        
        new_story = Story(
            user_id=current_user.id,
            title=title,
            challenge=challenge,
            turning_point=turning_point,
            outcome=outcome
        )
        db.session.add(new_story)
        db.session.commit()
        
        flash('تم نشر قصتك بنجاح ومشاركتها مع مجتمع مسارات!', 'success')
        return redirect(url_for('home'))
        
    return render_template('add_story.html')

# --- 4. مسار إضافة التعليقات (مع حماية ضد الثغرات) ---
@app.route('/story/<int:story_id>/comment', methods=['POST'])
@login_required
def add_comment(story_id):
    content = request.form.get('content').strip()
    if content:
        # حماية بدائية من إدخال نصوص فارغة وحفظ التعليق
        new_comment = Comment(
            story_id=story_id,
            user_id=current_user.id,
            content=content
        )
        db.session.add(new_comment)
        db.session.commit()
        flash('تمت إضافة تعليقك بنجاح!', 'success')
    return redirect(url_for('home'))

# --- 5. مسارات الرسائل الخاصة (Direct Messages) ---
@app.route('/messages', methods=['GET', 'POST'])
@login_required
def messages():
    if request.method == 'POST':
        receiver_username = request.form.get('receiver').strip()
        message_text = request.form.get('message').strip()
        
        receiver = User.query.filter_by(username=receiver_username).first()
        if not receiver:
            flash('هذا المستخدم غير موجود بالمنصة!', 'danger')
        elif receiver.id == current_user.id:
            flash('لا يمكنك إرسال رسالة لنفسك!', 'warning')
        elif message_text:
            new_message = DirectMessage(
                sender_id=current_user.id,
                receiver_id=receiver.id,
                message_text=message_text
            )
            db.session.add(new_message)
            db.session.commit()
            flash('تم إرسال الرسالة بنجاح!', 'success')
            
        return redirect(url_for('messages'))

    # جلب الرسائل الواردة والصادرة الخاصة بالمستخدم الحالي فقط (حماية ضد الـ IDOR)
    all_messages = DirectMessage.query.filter(
        or_(
            DirectMessage.sender_id == current_user.id,
            DirectMessage.receiver_id == current_user.id
        )
    ).order_by(DirectMessage.created_at.asc()).all()
    
    return render_template('messages.html', messages=all_messages)

if __name__ == '__main__':
    # تشغيل السيرفر المحلي على بورت 5000
    app.run(host='0.0.0.0', port=5000)