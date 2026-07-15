import os
from datetime import datetime, date
from flask import Flask, render_template, redirect, url_for, request, flash, session, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Story, Comment, DirectMessage, Like, Group, GroupMessage, Block, Report
from sqlalchemy import or_

app = Flask(__name__)

# إعدادات الحماية والـ Session
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'Fawzi_Secure_DevSecOps_Key_2026')

# --- فرض رابط قاعدة البيانات الجديدة برمجياً لتخطي تعليق الكاش على Render ---
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

# بناء وتحديث الجداول بأمان تام دون التسبب في انهيار السيرفر (Error 500)
with app.app_context():
    try:
        # ملاحظة: إذا أردت تصفير البيانات كلياً لتطبيق الأعمدة الجديدة، قم بتفعيل السطر التالي لمرة واحدة فقط ثم احذفه
        # db.drop_all() 
        db.create_all()
        
        # جعل حسابك الافتراضي (fawzi) أدمن تلقائياً إن وجد
        fawzi_admin = User.query.filter_by(username='fawzi').first()
        if fawzi_admin:
            fawzi_admin.is_admin = True
            db.session.commit()
    except Exception as db_err:
        print(f"⚠️ DATABASE INITIALIZATION ERROR: {db_err}")

# التحقق من الإيميلات الوهمية
def is_disposable_email(email):
    disposable_domains = ['mailinator.com', 'tempmail.com', 'yopmail.com', '10minutemail.com', 'sharklasers.com', 'guerrillamail.com']
    domain = email.split('@')[-1].lower() if '@' in email else ''
    return domain in disposable_domains

# حساب السن الحقيقي للمستخدم
def calculate_age(birth_date):
    if not birth_date:
        return 0
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

# --- 1. المسار الرئيسي (تم حل مشكلة الترجمة t) ---
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
    show_welcome = not current_user.is_authenticated
    return render_template('home.html', stories=stories, show_welcome=show_welcome, t=t)

# --- 2. التسجيل والتحقق من الهوية ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
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
            flash('التسجيل باستخدام بريد إلكتروني وهمي أو مؤقت غير مسموح به لحماية المجتمع!', 'danger')
            return redirect(url_for('register'))
            
        if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            flash('اسم المستخدم أو البريد الإلكتروني مسجل بالفعل بالمنصة!', 'danger')
            return redirect(url_for('register'))
            
        try:
            birth_date = datetime.strptime(birth_str, '%Y-%m-%d').date()
        except:
            flash('تاريخ الميلاد غير صحيح!', 'danger')
            return redirect(url_for('register'))
            
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
        
        flash('تم إنشاء حسابك بنجاح! يسعدنا انضمامك.', 'success')
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
            login_user(user, remember=True)
            flash('أهلاً بك مجدداً في منصتك!', 'success')
            return redirect(url_for('home'))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة!', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('تم تسجيل الخروج بنجاح وتأمين جلستك.', 'info')
    return redirect(url_for('home'))

# --- 3. كتابة قصة ---
@app.route('/add-story', methods=['GET', 'POST'])
@login_required
def add_story():
    if calculate_age(current_user.birth_date) < 18:
        flash('مرحباً بك! يتطلب نشر القصص والمشاركة في المنصة بلوغ 18 عاماً كحد أدنى للأمان والخصوصية.', 'warning')
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        title = request.form.get('title').strip()
        challenge = request.form.get('challenge').strip()
        turning_point = request.form.get('turning_point').strip()
        outcome = request.form.get('outcome').strip()
        
        new_story = Story(
            user_id=current_user.id, title=title, challenge=challenge,
            turning_point=turning_point, outcome=outcome
        )
        db.session.add(new_story)
        db.session.commit()
        flash('تم نشر مسار نجاحك وإلهام الآخرين بنجاح!', 'success')
        return redirect(url_for('home'))
        
    return render_template('add_story.html')

# --- 4. الشات والمراسلات المتقدمة ---
@app.route('/messages', methods=['GET', 'POST'])
@login_required
def messages():
    if calculate_age(current_user.birth_date) < 18:
        flash('عذراً، استخدام غرف التواصل متاح فقط للأعضاء فوق 18 عاماً لحماية خصوصية الجميع.', 'warning')
        return redirect(url_for('home'))

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
            receiver_username = request.form.get('receiver').strip()
            message_text = request.form.get('message', '').strip()
            receiver = User.query.filter_by(username=receiver_username).first()
            
            if receiver:
                has_blocked = Block.query.filter(
                    or_(
                        (Block.blocker_id == current_user.id) & (Block.blocked_id == receiver.id),
                        (Block.blocker_id == receiver.id) & (Block.blocked_id == current_user.id)
                    )
                ).first()
                
                if has_blocked:
                    flash('لا يمكن إرسال الرسالة، تم فرض حظر الخصوصية بين الحسابين.', 'danger')
                    return redirect(url_for('messages', tab='private'))
                    
                if message_text or 'voice_file' in request.files:
                    new_message = DirectMessage(
                        sender_id=current_user.id, receiver_id=receiver.id, message_text=message_text
                    )
                    db.session.add(new_message)
                    db.session.commit()
                    return redirect(url_for('messages', tab='private', **{'with': receiver_username}))

        elif chat_type == 'group':
            group_id = request.form.get('group_id')
            message_text = request.form.get('message', '').strip()
            group = Group.query.get(group_id)
            if group and message_text:
                new_gmsg = GroupMessage(
                    group_id=group.id, sender_id=current_user.id, message_text=message_text
                )
                db.session.add(new_gmsg)
                db.session.commit()
                return redirect(url_for('messages', tab='groups', group_id=group_id))

    if chatting_with_username:
        other_user = User.query.filter_by(username=chatting_with_username).first()
        if other_user:
            private_messages = DirectMessage.query.filter(
                or_(
                    (DirectMessage.sender_id == current_user.id) & (DirectMessage.receiver_id == other_user.id),
                    (DirectMessage.sender_id == other_user.id) & (DirectMessage.receiver_id == current_user.id)
                )
            ).order_by(DirectMessage.created_at.asc()).all()

    if selected_group_id:
        group_messages = GroupMessage.query.filter_by(group_id=selected_group_id).order_by(GroupMessage.created_at.asc()).all()

    return render_template('messages.html', 
                           all_users=all_users, my_groups=my_groups,
                           private_messages=private_messages, group_messages=group_messages,
                           active_tab=active_tab, chatting_with=chatting_with_username,
                           selected_group_id=selected_group_id)

# --- 5. مسار مسح محادثة بالكامل ---
@app.route('/clear-chat/<username>', methods=['POST'])
@login_required
def clear_chat(username):
    other_user = User.query.filter_by(username=username).first_or_404()
    messages_to_delete = DirectMessage.query.filter(
        or_(
            (DirectMessage.sender_id == current_user.id) & (DirectMessage.receiver_id == other_user.id),
            (DirectMessage.sender_id == other_user.id) & (DirectMessage.receiver_id == current_user.id)
        )
    ).all()
    for msg in messages_to_delete:
        db.session.delete(msg)
    db.session.commit()
    flash('تم مسح سجل المحادثة بالكامل بنجاح.', 'success')
    return redirect(url_for('messages', tab='private'))

# --- 6. الملف الشخصي العام للمستخدم ---
@app.route('/profile/<username>')
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    user_stories = Story.query.filter_by(user_id=user.id).all()
    
    is_blocked = False
    if current_user.is_authenticated:
        is_blocked = Block.query.filter_by(blocker_id=current_user.id, blocked_id=user.id).first() is not None
        
    return render_template('profile.html', user=user, stories=user_stories, is_blocked=is_blocked)

# --- 7. نظام الحظر وفك الحظر ---
@app.route('/block/<int:user_id>', methods=['POST'])
@login_required
def block_user(user_id):
    if current_user.id == user_id:
        flash('لا يمكنك حظر حسابك الخاص!', 'warning')
        return redirect(url_for('home'))
        
    existing_block = Block.query.filter_by(blocker_id=current_user.id, blocked_id=user_id).first()
    if not existing_block:
        new_block = Block(blocker_id=current_user.id, blocked_id=user_id)
        db.session.add(new_block)
        db.session.commit()
        flash('تم حظر الحساب بنجاح وتأمين خصوصيتك.', 'success')
    return redirect(request.referrer or url_for('home'))

@app.route('/unblock/<int:user_id>', methods=['POST'])
@login_required
def unblock_user(user_id):
    block = Block.query.filter_by(blocker_id=current_user.id, blocked_id=user_id).first()
    if block:
        db.session.delete(block)
        db.session.commit()
        flash('تم فك الحظر بنجاح ويمكنكم التواصل الآن.', 'success')
    return redirect(request.referrer or url_for('home'))

# --- 8. تقديم البلاغات ---
@app.route('/report', methods=['POST'])
@login_required
def submit_report():
    reported_user_id = request.form.get('reported_user_id')
    story_id = request.form.get('story_id')
    reason = request.form.get('reason').strip()
    
    new_report = Report(
        reporter_id=current_user.id,
        reported_user_id=reported_user_id if reported_user_id else None,
        story_id=story_id if story_id else None,
        reason=reason
    )
    db.session.add(new_report)
    db.session.commit()
    flash('تم رفع البلاغ بنجاح للجنة الإشراف، وسنتعامل معه بسرية تامة.', 'success')
    return redirect(request.referrer or url_for('home'))

# --- 9. لوحة تحكم الإشراف للأدمن ---
@app.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin:
        abort(403)
    
    users = User.query.all()
    reports = Report.query.order_by(Report.created_at.desc()).all()
    stories = Story.query.all()
    return render_template('admin.html', users=users, reports=reports, stories=stories)

@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    if not current_user.is_admin:
        abort(403)
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('تم شطب وحظر العضو من المنصة نهائياً بقرار إداري.', 'danger')
    return redirect(url_for('admin_panel'))

# مسار إنشاء مجموعة جديدة
@app.route('/create-group', methods=['POST'])
@login_required
def create_group():
    group_name = request.form.get('group_name').strip()
    if group_name:
        existing = Group.query.filter_by(name=group_name).first()
        if existing:
            flash('اسم المجموعة مستخدم بالفعل!', 'warning')
        else:
            new_group = Group(name=group_name, created_by=current_user.id)
            new_group.members.append(current_user)
            db.session.add(new_group)
            db.session.commit()
            flash(f'تم إنشاء مجموعة "{group_name}" بنجاح!', 'success')
    return redirect(url_for('messages', tab='groups'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)