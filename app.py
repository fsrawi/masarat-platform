import os
from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Story, Comment, DirectMessage, Like
from sqlalchemy import or_

app = Flask(__name__)

# إعدادات الحماية والـ Session
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'Fawzi_Secure_DevSecOps_Key_2026')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///masarat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

# حقن متغيرات إضافية في جميع الواجهات تلقائياً (مثل وجود رسائل غير مقروءة واللغة الحالية)
@app.context_processor
def inject_global_vars():
    has_unread = False
    if current_user.is_authenticated:
        # فحص إذا كان هناك أي رسالة موجهة للمستخدم الحالي لم تُقرأ بعد
        unread_count = DirectMessage.query.filter_by(receiver_id=current_user.id, is_read=False).count()
        has_unread = unread_count > 0
    
    # تحديد لغة الموقع الافتراضية (عربي 'ar' إن لم تكن محددة في الجلسة)
    current_lang = session.get('lang', 'ar')
    return dict(has_unread_messages=has_unread, current_lang=current_lang)


# --- مسار تبديل اللغة (AR/EN Toggle) ---
@app.route('/toggle-lang')
def toggle_lang():
    # تبديل اللغة المخزنة في الـ Session للجهاز الحالي
    old_lang = session.get('lang', 'ar')
    session['lang'] = 'en' if old_lang == 'ar' else 'ar'
    return redirect(request.referrer or url_for('home'))


# --- 1. المسار الرئيسي (عرض القصص والتعليقات ديناميكياً) ---
@app.route('/')
def home():
    stories = Story.query.order_by(Story.created_at.desc()).all()
    
    # لغة العرض الحالية
    lang = session.get('lang', 'ar')
    
    # مصفوفة الترجمة الثابتة للعناصر الأساسية بالواجهة بالاسم الجديد "منصة نجاحي هو نجاحك"
    translations = {
        'ar': {
            'title': 'منصة نجاحي هو نجاحك - قصص ملهمة',
            'brand': 'منصة نجاحي هو نجاحك',
            'welcome': 'مرحباً،',
            'create_story': 'أنشئ قصتك',
            'messages': 'الرسائل الخاصة',
            'logout': 'خروج',
            'login': 'تسجيل الدخول',
            'register': 'إنشاء حساب',
            'main_heading': 'قصص ملهمة في مواجهة التحديات',
            'no_stories': 'لا توجد قصص منشورة بعد، كن أول من ينشر قصة نجاحه!',
            'published_by': 'نُشرت بواسطة:',
            'challenge': 'مرحلة الصعوبة والتحدي',
            'turning_point': 'نقطة التحول والنجاح',
            'outcome': 'النتيجة الحالية والدروس',
            'comments': 'التعليقات',
            'no_comments': 'لا توجد تعليقات بعد. كن أول من يعلق!',
            'add_comment_placeholder': 'اكتب تعليقاً مشجعاً...',
            'comment_btn': 'تعليق',
            'login_to_comment': 'سجل دخولك لتستطيع التفاعل وكتابة تعليق.'
        },
        'en': {
            'title': 'My Success is Your Success - Inspiring Stories',
            'brand': 'My Success is Your Success',
            'welcome': 'Welcome,',
            'create_story': 'Create Story',
            'messages': 'Direct Messages',
            'logout': 'Logout',
            'login': 'Login',
            'register': 'Register',
            'main_heading': 'Inspiring Stories in the Face of Challenges',
            'no_stories': 'No stories published yet. Be the first to share your success!',
            'published_by': 'Published by:',
            'challenge': 'Difficulty & Challenge Stage',
            'turning_point': 'The Turning Point & Success',
            'outcome': 'Current Outcome & Lessons',
            'comments': 'Comments',
            'no_comments': 'No comments yet. Be the first to comment!',
            'add_comment_placeholder': 'Write an encouraging comment...',
            'comment_btn': 'Comment',
            'login_to_comment': 'Log in to interact and leave a comment.'
        }
    }
    
    t = translations[lang]
    return render_template('home.html', stories=stories, t=t)


# --- 2. مسارات تسجيل الدخول والحسابات (Authentication) ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        username = request.form.get('username').strip()
        email = request.form.get('email').strip()
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            flash('اسم المستخدم أو البريد الإلكتروني مسجل بالفعل!', 'danger')
            return redirect(url_for('register'))
            
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        
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


# --- 4. مسار إضافة التعليقات ---
@app.route('/story/<int:story_id>/comment', methods=['POST'])
@login_required
def add_comment(story_id):
    content = request.form.get('content').strip()
    if content:
        new_comment = Comment(
            story_id=story_id,
            user_id=current_user.id,
            content=content
        )
        db.session.add(new_comment)
        db.session.commit()
        flash('تمت إضافة تعليقك بنجاح!', 'success')
    return redirect(url_for('home'))


# --- 5. مسار التفاعل بالإعجاب (Like Toggle) ---
@app.route('/story/<int:story_id>/like', methods=['POST'])
@login_required
def like_story(story_id):
    existing_like = Like.query.filter_by(user_id=current_user.id, story_id=story_id).first()
    
    if existing_like:
        db.session.delete(existing_like)
        db.session.commit()
    else:
        new_like = Like(user_id=current_user.id, story_id=story_id)
        db.session.add(new_like)
        db.session.commit()
        
    return redirect(url_for('home'))


# --- 6. مسارات الرسائل الخاصة ---
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

    all_messages = DirectMessage.query.filter(
        or_(
            DirectMessage.sender_id == current_user.id,
            DirectMessage.receiver_id == current_user.id
        )
    ).order_by(DirectMessage.created_at.asc()).all()
    
    unread_messages = DirectMessage.query.filter_by(receiver_id=current_user.id, is_read=False).all()
    for msg in unread_messages:
        msg.is_read = True
    db.session.commit()
    
    return render_template('messages.html', messages=all_messages)


# --- التشغيل البرمجي وتحديد المنفذ (Port Binding) ديناميكياً لـ Render ---
if __name__ == '__main__':
    # جلب المنفذ ديناميكياً من خادم Render، وإن لم يكن متوفراً يتم التعيين افتراضياً على 10000
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)