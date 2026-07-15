import os
from datetime import datetime, date
from flask import Flask, render_template, redirect, url_for, request, flash, session, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from models import db, User, Story, Comment, DirectMessage, Like, Group, GroupMessage, Block, Report
from sqlalchemy import or_

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'Fawzi_Secure_DevSecOps_Key_2026')

app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

database_url = "postgresql://masarat_db_new_user:CedqCPmLtuiZKC4en8nYcguEZr33CAdP@dpg-d9bu85mcjfls739n0di0-a/masarat_db_new"
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    try:
        # تم إيقاف المسح للحفاظ على بياناتك
        # db.drop_all() 
        db.create_all() 
        fawzi_admin = User.query.filter_by(username='fawzi').first()
        if fawzi_admin:
            fawzi_admin.is_admin = True
            db.session.commit()
    except Exception as db_err:
        print(f"⚠️ DATABASE ERROR: {db_err}")

def is_disposable_email(email):
    disposable_domains = ['mailinator.com', 'tempmail.com', 'yopmail.com']
    domain = email.split('@')[-1].lower() if '@' in email else ''
    return domain in disposable_domains

def calculate_age(birth_date):
    if not birth_date: return 18 
    if isinstance(birth_date, str):
        try: birth_date = datetime.strptime(birth_date.split(' ')[0], '%Y-%m-%d').date()
        except: return 18
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

@app.context_processor
def inject_global_vars():
    has_unread = False
    is_underage = False
    if current_user.is_authenticated:
        try: has_unread = DirectMessage.query.filter_by(receiver_id=current_user.id, is_read=False).count() > 0
        except: pass
        if current_user.birth_date: is_underage = calculate_age(current_user.birth_date) < 18
    return dict(has_unread_messages=has_unread, current_lang=session.get('lang', 'ar'), is_underage=is_underage)

@app.route('/toggle-lang')
def toggle_lang():
    session['lang'] = 'en' if session.get('lang', 'ar') == 'ar' else 'ar'
    return redirect(request.referrer or url_for('home'))

@app.route('/')
def home():
    try: stories = Story.query.order_by(Story.created_at.desc()).all()
    except: stories = []
    
    t = {
        'ar': {'title': 'منصة نجاحي', 'brand': 'منصة نجاحي', 'create_story': 'أنشئ قصتك', 'messages': 'الرسائل', 'profile': 'ملفي', 'logout': 'خروج', 'login': 'دخول', 'register': 'حساب جديد', 'main_heading': 'مسارات وتجارب ملهمة', 'no_stories': 'لا توجد قصص بعد.'},
        'en': {'title': 'My Success', 'brand': 'My Success', 'create_story': 'Create Story', 'messages': 'Messages', 'profile': 'Profile', 'logout': 'Logout', 'login': 'Login', 'register': 'Register', 'main_heading': 'Inspiring Paths', 'no_stories': 'No stories yet.'}
    }[session.get('lang', 'ar')]
    
    return render_template('home.html', stories=stories, show_welcome=not current_user.is_authenticated, t=t)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated: return redirect(url_for('home'))
    if request.method == 'POST':
        email = request.form.get('email').strip()
        if is_disposable_email(email):
            flash('البريد الوهمي غير مسموح!', 'danger')
            return redirect(url_for('register'))
            
        try: birth_date = datetime.strptime(request.form.get('birth_date'), '%Y-%m-%d').date()
        except: birth_date = date(2000, 1, 1)
            
        new_user = User(
            username=request.form.get('username').strip(), email=email,
            phone=request.form.get('phone').strip(), birth_date=birth_date,
            country=request.form.get('country').strip(), city=request.form.get('city').strip(),
            occupation_type=request.form.get('occupation_type'),
            university_name=request.form.get('university_name', '').strip(),
            company_name=request.form.get('company_name', '').strip()
        )
        new_user.set_password(request.form.get('password'))
        db.session.add(new_user)
        db.session.commit()
        flash('تم التسجيل بنجاح!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('home'))
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username').strip()).first()
        if user and user.check_password(request.form.get('password')):
            login_user(user, remember=True)
            return redirect(url_for('home'))
        flash('بيانات غير صحيحة!', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/add-story', methods=['GET', 'POST'])
@login_required
def add_story():
    try:
        if calculate_age(current_user.birth_date) < 18:
            flash('نشر القصص يتطلب عمر 18 عاماً فأكثر.', 'warning')
            return redirect(url_for('home'))
    except: pass
        
    if request.method == 'POST':
        new_story = Story(user_id=current_user.id, title=request.form.get('title', ''), challenge=request.form.get('challenge', ''), turning_point=request.form.get('turning_point', ''), outcome=request.form.get('outcome', ''))
        db.session.add(new_story)
        db.session.commit()
        flash('تم النشر!', 'success')
        return redirect(url_for('home'))
    return render_template('add_story.html')

# --- التفاعل مع القصص ---
@app.route('/story/<int:story_id>/like', methods=['POST'])
@login_required
def like_story(story_id):
    existing_like = Like.query.filter_by(user_id=current_user.id, story_id=story_id).first()
    if existing_like:
        db.session.delete(existing_like)
    else:
        db.session.add(Like(user_id=current_user.id, story_id=story_id))
    db.session.commit()
    return redirect(request.referrer or url_for('home'))

@app.route('/story/<int:story_id>/comment', methods=['POST'])
@login_required
def add_comment(story_id):
    content = request.form.get('content').strip()
    if content:
        db.session.add(Comment(story_id=story_id, user_id=current_user.id, content=content))
        db.session.commit()
    return redirect(request.referrer or url_for('home'))

# --- الشات المحسن ---
@app.route('/messages', methods=['GET', 'POST'])
@login_required
def messages():
    active_tab = request.args.get('tab', 'private')
    chatting_with = request.args.get('with', '')
    selected_group_id = request.args.get('group_id', '')
    
    if request.method == 'POST':
        chat_type = request.form.get('chat_type')
        if chat_type == 'private':
            receiver = User.query.filter_by(username=request.form.get('receiver', '').strip()).first()
            msg = request.form.get('message', '').strip()
            if receiver and msg:
                db.session.add(DirectMessage(sender_id=current_user.id, receiver_id=receiver.id, message_text=msg))
                db.session.commit()
                return redirect(url_for('messages', tab='private', **{'with': receiver.username}))
        elif chat_type == 'group':
            group = Group.query.get(request.form.get('group_id'))
            msg = request.form.get('message', '').strip()
            if group and msg:
                db.session.add(GroupMessage(group_id=group.id, sender_id=current_user.id, message_text=msg))
                db.session.commit()
                return redirect(url_for('messages', tab='groups', group_id=group.id))

    # تحديد الرسائل كمقروءة
    if chatting_with:
        other = User.query.filter_by(username=chatting_with).first()
        if other:
            unread = DirectMessage.query.filter_by(sender_id=other.id, receiver_id=current_user.id, is_read=False).all()
            for u in unread: u.is_read = True
            db.session.commit()
            private_msgs = DirectMessage.query.filter(
                or_((DirectMessage.sender_id == current_user.id) & (DirectMessage.receiver_id == other.id),
                    (DirectMessage.sender_id == other.id) & (DirectMessage.receiver_