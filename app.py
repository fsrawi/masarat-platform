import os
from datetime import datetime, date
from flask import Flask, render_template, redirect, url_for, request, flash, session, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Story, Comment, DirectMessage, Like, Group, GroupMessage, Block, Report
from sqlalchemy import or_

app = Flask(__name__)

# إعدادات الحماية والـ Session
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'Fawzi_Secure_DevSecOps_Key_2026')

# --- رابط قاعدة البيانات المباشر ---
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

# بناء وتحديث الجداول
with app.app_context():
    try:
        db.drop_all() # مسح الجداول القديمة المتعارضة
        db.create_all() # بناء الجداول الجديدة المحدثة
        fawzi_admin = User.query.filter_by(username='fawzi').first()
        if fawzi_admin:
            fawzi_admin.is_admin = True
            db.session.commit()
    except Exception as db_err:
        print(f"⚠️ DATABASE INITIALIZATION ERROR: {db_err}")

def is_disposable_email(email):
    disposable_domains = ['mailinator.com', 'tempmail.com', 'yopmail.com', '10minutemail.com', 'sharklasers.com', 'guerrillamail.com']
    domain = email.split('@')[-1].lower() if '@' in email else ''
    return domain in disposable_domains

# --- حماية دالة العمر من الانهيار إذا كان الحقل فارغاً ---
def calculate_age(birth_date):
    if not birth_date:
        return 18 # قيمة افتراضية آمنة
    if isinstance(birth_date, str):
        try:
            birth_date = datetime.strptime(birth_date.split(' ')[0], '%Y-%m-%d').date()
        except:
            return 18
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

@app.context_processor
def inject_global_vars():
    has_unread = False
    is_underage = False
    if current_user.is_authenticated:
        try:
            unread_count = DirectMessage.query.filter_by(receiver_id=current_user.id, is_read=False).count()
            has_unread = unread_count > 0
        except:
            has_unread = False
            
        if current_user.birth_date:
            is_underage = calculate_age(current_user.birth_date) < 18
            
    current_lang = session.get('lang', 'ar')
    return dict(has_unread_messages=has_unread, current_lang=current_lang, is_underage=is_underage)

@app.route('/toggle-lang')
def toggle_lang():
    old_lang = session.get('lang', 'ar')
    session['lang'] = 'en' if old_lang == 'ar' else 'ar'
    return redirect(request.referrer or url_for('home'))

@app.route('/')
def home():
    try:
        stories = Story.query.order_by(Story.created_at.desc()).all()
    except Exception as e:
        stories = []
        print(f"Query error: {e}")
        
    lang = session.get('lang', 'ar')
    translations = {
        'ar': {
            'title': 'منصة نجاحي هو نجاحك - قصص ملهمة', 'brand': 'منصة نجاحي هو نجاحك',
            'welcome': 'مرحباً،', 'create_story': 'أنشئ قصتك', 'messages': 'الرسائل الخاصة',
            'profile': 'ملفي الشخصي', 'logout': 'خروج', 'login': 'تسجيل الدخول', 'register': 'إنشاء حساب',
            'main_heading': 'قصص ملهمة في مواجهة التحديات', 'no_stories': 'لا توجد قصص منشورة بعد، كن أول من ينشر قصة نجاحه!',
            'published_by': 'نُشرت بواسطة:', 'challenge': 'مرحلة الصعوبة والتحدي',
            'turning_point': 'نقطة التحول والنجاح', 'outcome': 'النتيجة الحالية والدروس',
            'comments': 'التعليقات', 'no_comments': 'لا توجد تعليقات بعد. كن أول من يعلق!',
            'add_comment_placeholder': 'اكتب تعليقاً مشجعاً...', 'comment_btn': 'تعليق',
            'login_to_comment': 'سجل دخولك لتستطيع التفاعل وكتابة تعليق.'
        },
        'en': {
            'title': 'My Success is Your Success', 'brand': 'My Success is Your Success',
            'welcome': 'Welcome,', 'create_story': 'Create Story', 'messages': 'Messages',
            'profile': 'My Profile', 'logout': 'Logout', 'login': 'Login', 'register': 'Register',
            'main_heading': 'Inspiring Stories', 'no_stories': 'No stories published yet.',
            'published_by': 'Published by:', 'challenge': 'Challenge',
            'turning_point': 'Turning Point', 'outcome': 'Outcome',
            'comments': 'Comments', 'no_comments': 'No comments yet.',
            'add_comment_placeholder': 'Write a comment...', 'comment_btn': 'Comment',
            'login_to_comment': 'Log in to comment.'
        }
    }
    t = translations[lang]
    show_welcome = not current_user.is_authenticated
    return render_template('home.html', stories=stories, show_welcome=show_welcome, t=t)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated: return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form.get('username').strip()
        email = request.form.get('email').strip()
        password = request.form.get('password')
        phone = request.form.get('phone').strip()
        birth_str = request.form.get('birth_date')
        country = request.form.get('country').strip()
        city = request.form.get('city').strip()
        occupation = request.form.get('occupation_type')
        university = request.form.get('university_name', '').strip()
        company = request.form.get('company_name', '').strip()
        show_email = 'show_email' in request.form
        show_phone = 'show_phone' in request.form
        
        if is_disposable_email(email):
            flash('البريد الوهمي غير مسموح!', 'danger')
            return redirect(url_for('register'))
        if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            flash('البيانات مسجلة مسبقاً!', 'danger')
            return redirect(url_for('register'))
            
        try:
            birth_date = datetime.strptime(birth_str, '%Y-%m-%d').date()
        except:
            birth_date = date(2000, 1, 1) # حماية افتراضية
            
        new_user = User(
            username=username, email=email, phone=phone, birth_date=birth_date,
            country=country, city=city, occupation_type=occupation,
            university_name=university if occupation == 'student' else None,
            company_name=company if occupation == 'employee' else None,
            show_email=show_email, show_phone=show_phone
        )
        new_user.set_password(password)
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

# --- حماية مسار نشر القصة من الخطأ 500 ---
@app.route('/add-story', methods=['GET', 'POST'])
@login_required
def add_story():
    try:
        if calculate_age(current_user.birth_date) < 18:
            flash('نشر القصص يتطلب عمر 18 عاماً فأكثر.', 'warning')
            return redirect(url_for('home'))
    except:
        pass
        
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        challenge = request.form.get('challenge', '').strip()
        turning_point = request.form.get('turning_point', '').strip()
        outcome = request.form.get('outcome', '').strip()
        
        if not title or not challenge:
            flash('يرجى تعبئة الحقول الأساسية!', 'danger')
            return redirect(url_for('add_story'))
            
        new_story = Story(user_id=current_user.id, title=title, challenge=challenge, turning_point=turning_point, outcome=outcome)
        db.session.add(new_story)
        db.session.commit()
        flash('تم نشر القصة بنجاح!', 'success')
        return redirect(url_for('home'))
    return render_template('add_story.html')

@app.route('/messages', methods=['GET', 'POST'])
@login_required
def messages():
    active_tab = request.args.get('tab', 'private')
    chatting_with_username = request.args.get('with', '')
    selected_group_id = request.args.get('group_id', '')
    all_users = User.query.filter(User.id != current_user.id).all()
    my_groups = Group.query.all()
    private_messages = []
    group_messages = []

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

    if chatting_with_username:
        other = User.query.filter_by(username=chatting_with_username).first()
        if other:
            private_messages = DirectMessage.query.filter(
                or_((DirectMessage.sender_id == current_user.id) & (DirectMessage.receiver_id == other.id),
                    (DirectMessage.sender_id == other.id) & (DirectMessage.receiver_id == current_user.id))
            ).order_by(DirectMessage.created_at.asc()).all()

    if selected_group_id:
        group_messages = GroupMessage.query.filter_by(group_id=selected_group_id).order_by(GroupMessage.created_at.asc()).all()

    return render_template('messages.html', all_users=all_users, my_groups=my_groups, private_messages=private_messages, group_messages=group_messages, active_tab=active_tab, chatting_with=chatting_with_username, selected_group_id=selected_group_id)

@app.route('/create-group', methods=['POST'])
@login_required
def create_group():
    group_name = request.form.get('group_name').strip()
    if group_name and not Group.query.filter_by(name=group_name).first():
        new_group = Group(name=group_name, created_by=current_user.id)
        db.session.add(new_group)
        db.session.commit()
    return redirect(url_for('messages', tab='groups'))

@app.route('/profile/<username>')
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    stories = Story.query.filter_by(user_id=user.id).all()
    is_blocked = Block.query.filter_by(blocker_id=current_user.id, blocked_id=user.id).first() is not None
    return render_template('profile.html', user=user, stories=stories, is_blocked=is_blocked)

@app.route('/block/<int:user_id>', methods=['POST'])
@login_required
def block_user(user_id):
    if current_user.id != user_id and not Block.query.filter_by(blocker_id=current_user.id, blocked_id=user_id).first():
        db.session.add(Block(blocker_id=current_user.id, blocked_id=user_id))
        db.session.commit()
    return redirect(request.referrer or url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))