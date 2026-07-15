import os
import traceback
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
        db.create_all() 
    except Exception as db_err:
        print(f"⚠️ DATABASE ERROR: {db_err}")

# حماية الحساب الجذري لفوزي
@app.before_request
def auto_admin():
    try:
        if current_user.is_authenticated and current_user.username.lower() == 'fawzi':
            if not current_user.is_admin:
                current_user.is_admin = True
                db.session.commit()
    except:
        pass

def is_disposable_email(email):
    disposable_domains = ['mailinator.com', 'tempmail.com', 'yopmail.com']
    return (email.split('@')[-1].lower() if '@' in email else '') in disposable_domains

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
        try: 
            has_unread = DirectMessage.query.filter_by(receiver_id=current_user.id, is_read=False).count() > 0
            if hasattr(current_user, 'birth_date') and current_user.birth_date:
                is_underage = calculate_age(current_user.birth_date) < 18
        except: pass
    return dict(has_unread_messages=has_unread, current_lang=session.get('lang', 'ar'), is_underage=is_underage)

@app.route('/toggle-lang')
def toggle_lang():
    session['lang'] = 'en' if session.get('lang', 'ar') == 'ar' else 'ar'
    return redirect(request.referrer or url_for('home'))

@app.route('/')
def home():
    try:
        try: stories = Story.query.order_by(Story.created_at.desc()).all()
        except: stories = []
        
        t = {
            'ar': {
                'title': 'منصة نجاحي', 'brand': 'منصة نجاحي', 'create_story': 'أنشئ قصتك', 
                'messages': 'الرسائل', 'profile': 'ملفي', 'logout': 'خروج', 'login': 'دخول', 
                'register': 'حساب جديد', 'main_heading': 'مسارات وتجارب ملهمة', 
                'no_stories': 'لا توجد قصص بعد.', 'published_by': 'بواسطة:', 
                'challenge': 'التحدي', 'turning_point': 'التحول', 'outcome': 'النتيجة',
                'comments': 'التعليقات', 'add_comment_placeholder': 'اكتب تعليقاً...', 
                'comment_btn': 'إرسال', 'no_comments': 'لا توجد تعليقات'
            },
            'en': {
                'title': 'My Success', 'brand': 'My Success', 'create_story': 'Create Story', 
                'messages': 'Messages', 'profile': 'Profile', 'logout': 'Logout', 
                'login': 'Login', 'register': 'Register', 'main_heading': 'Inspiring Paths', 
                'no_stories': 'No stories yet.', 'published_by': 'By:', 
                'challenge': 'Challenge', 'turning_point': 'Turning Point', 'outcome': 'Outcome',
                'comments': 'Comments', 'add_comment_placeholder': 'Write a comment...', 
                'comment_btn': 'Send', 'no_comments': 'No comments'
            }
        }[session.get('lang', 'ar')]
        
        return render_template('home.html', stories=stories, show_welcome=not current_user.is_authenticated, t=t)
    except Exception as e:
        return f"<div dir='ltr' style='background:#111; color:#ff4444; padding:20px; font-family:monospace;'><h3>🚨 ERROR:</h3><pre>{traceback.format_exc()}</pre></div>"

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated: return redirect(url_for('home'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        if is_disposable_email(email):
            flash('البريد الوهمي غير مسموح!', 'danger')
            return redirect(url_for('register'))
            
        try: birth_date = datetime.strptime(request.form.get('birth_date', ''), '%Y-%m-%d').date()
        except: birth_date = date(2000, 1, 1)
            
        new_user = User(
            username=request.form.get('username', '').strip(), email=email,
            phone=request.form.get('phone', '').strip(), birth_date=birth_date,
            country=request.form.get('country', '').strip(), city=request.form.get('city', '').strip(),
            occupation_type=request.form.get('occupation_type', 'student'),
            university_name=request.form.get('university_name', '').strip(),
            company_name=request.form.get('company_name', '').strip()
        )
        new_user.set_password(request.form.get('password', ''))
        db.session.add(new_user)
        db.session.commit()
        flash('تم التسجيل بنجاح!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('home'))
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username', '').strip()).first()
        if user and user.check_password(request.form.get('password', '')):
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
    if request.method == 'POST':
        new_story = Story(user_id=current_user.id, title=request.form.get('title', ''), challenge=request.form.get('challenge', ''), turning_point=request.form.get('turning_point', ''), outcome=request.form.get('outcome', ''))
        db.session.add(new_story)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('add_story.html')

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
    content = request.form.get('content', '').strip()
    if content:
        db.session.add(Comment(story_id=story_id, user_id=current_user.id, content=content))
        db.session.commit()
    return redirect(request.referrer or url_for('home'))

@app.route('/messages', methods=['GET', 'POST'])
@login_required
def messages():
    active_tab = request.args.get('tab', 'private')
    chatting_with = request.args.get('with', '')
    selected_group_id = request.args.get('group_id', '')
    
    if request.method == 'POST':
        chat_type = request.form.get('chat_type')
        voice = request.files.get('voice_file')
        voice_name = None
        
        if voice and voice.filename:
            filename = secure_filename(voice.filename)
            voice_name = f"voice_{int(datetime.utcnow().timestamp())}_{filename}"
            voice.save(os.path.join(app.config['UPLOAD_FOLDER'], voice_name))

        if chat_type == 'private':
            receiver = User.query.filter_by(username=request.form.get('receiver', '').strip()).first()
            msg = request.form.get('message', '').strip()
            if receiver and (msg or voice_name):
                db.session.add(DirectMessage(
                    sender_id=current_user.id, receiver_id=receiver.id, 
                    message_text=msg, voice_file=voice_name, is_voice=bool(voice_name)
                ))
                db.session.commit()
                return redirect(url_for('messages', tab='private', **{'with': receiver.username}))
                
        elif chat_type == 'group':
            group = Group.query.get(request.form.get('group_id'))
            msg = request.form.get('message', '').strip()
            if group and (msg or voice_name):
                db.session.add(GroupMessage(
                    group_id=group.id, sender_id=current_user.id, 
                    message_text=msg, voice_file=voice_name, is_voice=bool(voice_name)
                ))
                db.session.commit()
                return redirect(url_for('messages', tab='groups', group_id=group.id))

    private_msgs = []
    if chatting_with:
        other = User.query.filter_by(username=chatting_with).first()
        if other:
            private_msgs = DirectMessage.query.filter(
                or_((DirectMessage.sender_id == current_user.id) & (DirectMessage.receiver_id == other.id),
                    (DirectMessage.sender_id == other.id) & (DirectMessage.receiver_id == current_user.id))
            ).order_by(DirectMessage.created_at.asc()).all()

    group_msgs = []
    if selected_group_id:
        group_msgs = GroupMessage.query.filter_by(group_id=selected_group_id).order_by(GroupMessage.created_at.asc()).all()

    my_groups = current_user.chat_groups.all() if current_user.is_authenticated else []
    all_users = User.query.filter(User.id != current_user.id).all()

    return render_template('messages.html', 
                           all_users=all_users, 
                           my_groups=my_groups, 
                           private_messages=private_msgs, 
                           group_messages=group_msgs, 
                           active_tab=active_tab, chatting_with=chatting_with, selected_group_id=selected_group_id)

@app.route('/create-group', methods=['POST'])
@login_required
def create_group():
    group_name = request.form.get('group_name', '').strip()
    selected_users_ids = request.form.getlist('members') 
    
    if group_name and not Group.query.filter_by(name=group_name).first():
        new_group = Group(name=group_name, created_by=current_user.id)
        new_group.members.append(current_user) 
        
        for uid in selected_users_ids:
            try:
                user_to_add = User.query.get(int(uid))
                if user_to_add and user_to_add != current_user:
                    new_group.members.append(user_to_add)
            except: pass
                
        db.session.add(new_group)
        db.session.commit()
    return redirect(url_for('messages', tab='groups'))

@app.route('/delete-selected-messages', methods=['POST'])
@login_required
def delete_selected_messages():
    msg_ids = request.form.getlist('message_ids')
    is_group = request.form.get('is_group') == 'true'
    chatting_with = request.form.get('chatting_with', '')
    group_id = request.form.get('group_id', '')
    
    if msg_ids:
        ids_as_int = [int(i) for i in msg_ids]
        if is_group:
            GroupMessage.query.filter(GroupMessage.id.in_(ids_as_int), GroupMessage.sender_id == current_user.id).delete(synchronize_session=False)
        else:
            DirectMessage.query.filter(DirectMessage.id.in_(ids_as_int), DirectMessage.sender_id == current_user.id).delete(synchronize_session=False)
        db.session.commit()
        
    if is_group:
        return redirect(url_for('messages', tab='groups', group_id=group_id))
    return redirect(url_for('messages', tab='private', **{'with': chatting_with}))

@app.route('/profile/<username>')
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('profile.html', user=user, stories=Story.query.filter_by(user_id=user.id).all(), is_blocked=False)

@app.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        try:
            pic = request.files.get('profile_pic')
            if pic and pic.filename:
                filename = secure_filename(pic.filename)
                pic_name = f"{current_user.id}_{int(datetime.utcnow().timestamp())}_{filename}"
                pic.save(os.path.join(app.config['UPLOAD_FOLDER'], pic_name))
                current_user.profile_pic = pic_name
                
            current_user.bio = request.form.get('bio', '').strip()
            current_user.phone = request.form.get('phone', '').strip()
            current_user.country = request.form.get('country', '').strip()
            current_user.city = request.form.get('city', '').strip()
            
            current_user.show_email = 'show_email' in request.form
            current_user.show_phone = 'show_phone' in request.form
            
            db.session.commit()
            return redirect(url_for('profile', username=current_user.username))
        except Exception as e:
            return f"<h3 style='color:red;'>خطأ أثناء الحفظ: {e}</h3>"
            
    return render_template('edit_profile.html')

@app.route('/clear-chat/<username>', methods=['POST'])
@login_required
def clear_chat(username):
    other_user = User.query.filter_by(username=username).first_or_404()
    msgs = DirectMessage.query.filter(
        or_((DirectMessage.sender_id == current_user.id) & (DirectMessage.receiver_id == other_user.id),
            (DirectMessage.sender_id == other_user.id) & (DirectMessage.receiver_id == current_user.id))
    ).all()
    for m in msgs: db.session.delete(m)
    db.session.commit()
    return redirect(url_for('messages', tab='private'))

# مسار التهيئة لحل المشاكل بالكامل
@app.route('/setup-database-fawzi-2026')
def setup_database():
    try:
        db.drop_all()
        db.create_all()
        return "<h1 style='color:green; text-align:center; margin-top:50px;'>✅ تم تحديث وتهيئة قاعدة البيانات بنجاح! عد للرئيسية الآن.</h1>"
    except Exception as e:
        return f"<h1 style='color:red;'>خطأ: {e}</h1>"

@app.route('/admin')
@login_required
def admin_panel():
    try:
        if not current_user.is_admin: 
            abort(403)
        return render_template('admin.html', users=User.query.all())
    except Exception as e:
        return f"<div dir='ltr' style='background:#111; color:#ff4444; padding:20px; font-family:monospace;'><h3>🚨 ADMIN PANEL ERROR:</h3><pre>{traceback.format_exc()}</pre></div>"

@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    if not current_user.is_admin: abort(403)
    user = User.query.get_or_404(user_id)
    if user.username.lower() == 'fawzi':
        abort(400)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('admin_panel'))

@app.route('/admin/toggle-admin/<int:user_id>', methods=['POST'])
@login_required
def admin_toggle_admin(user_id):
    if not current_user.is_admin: 
        abort(403)
    user = User.query.get_or_404(user_id)
    
    if user.username.lower() == 'fawzi' or user.id == current_user.id:
        flash('خطأ: لا يمكن المساس بصلاحيات الحساب الجذري.', 'danger')
        return redirect(url_for('admin_panel'))
        
    user.is_admin = not user.is_admin
    db.session.commit()
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))