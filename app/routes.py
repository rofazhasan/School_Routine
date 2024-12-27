from flask import Blueprint, request, render_template, flash, redirect, url_for, session
from app.models import User,Class ,Subject,TeacherSchedule,News
from app.forms import LoginForm, AddUserForm,NewsForm,ChangePasswordForm,TeacherScheduleForm
from app.database import db
from datetime import datetime, time, timedelta,timezone
import pytz
from collections import defaultdict



app = Blueprint('app', __name__)


@app.route('/')
def index():
    return redirect(url_for('app.login'))


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        phone = form.phone_number.data
        password = form.password.data
        user = User.query.filter_by(phone=phone).first()
        if user and user.password == password:
            session['logged_in'] = True
            session['user_id'] = user.user_id
            session['user_role'] = user.role
            if session['user_role'] == 'Admin':
                return redirect(url_for('app.admin_dashboard'))
            else:
                return redirect(url_for('app.user_dashboard'))
        else:
            flash("Invalid phone or  password")
    return render_template('login.html', form=form)


@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if not session.get('logged_in'):
        return redirect(url_for('app.login'))

    form = ChangePasswordForm()
    user_id = session.get('user_id')
    user = User.query.filter_by(user_id=user_id).first()

    if form.validate_on_submit():
        old_password = form.old_password.data
        new_password = form.new_password.data

        # Check if the old password matches the stored password (without encryption)
        if user.password == old_password:
            # Update the user's password in the database (without encryption)
            user.password = new_password
            db.session.commit()

            flash('Password changed successfully!', 'success')
            if session['user_role'] == 'Admin':
                return redirect(url_for('app.admin_dashboard'))
            else:
                return redirect(url_for('app.user_dashboard'))  # Redirect to user dashboard
        else:
            flash('Incorrect old password.', 'danger')

    return render_template('change_password.html', form=form)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('user_id', None)
    session.pop('user_role', None)
    return redirect(url_for('app.login'))
    
@app.route('/show_routine', methods=['GET', 'POST'])
def show_routine():
    if not session.get('logged_in'):
        return redirect(url_for('app.login'))  # Replace 'app.login' with your login route
    user_id = session.get('user_id')
    user_role = session.get('user_role')

    selected_day = request.form.get('day_of_week') if request.method == 'POST' else None
    selected_class = request.form.get('class_id') if request.method == 'POST' else None
    selected_teacher = request.form.get('teacher_id') if request.method == 'POST' else None

    schedules = TeacherSchedule.query

    if user_role != 'Admin':
        schedules = schedules.filter_by(teacher_id=user_id)

    if selected_day:
        schedules = schedules.filter_by(day_of_week=selected_day)
    if selected_class:
        schedules = schedules.filter_by(class_id=int(selected_class))  # Convert selected_class to integer
    if selected_teacher:
        schedules = schedules.filter_by(teacher_id=int(selected_teacher))  # Convert selected_teacher to integer

    schedules = schedules.all()


    routine_data = defaultdict(list)
    for schedule in schedules:
        teacher = User.query.get(schedule.teacher_id)
        class_ = Class.query.get(schedule.class_id)
        subject = Subject.query.get(schedule.subject_id)
        routine_data[schedule.day_of_week].append({
            'teacher': teacher.name,
            'class': class_.class_name,
            'subject': subject.subject_name,
            'day': schedule.day_of_week,
            'start_time': schedule.start_time.strftime('%I:%M %p'),
            'end_time': schedule.end_time.strftime('%I:%M %p'),
            'user_role': teacher.role,
            'schedule_id': schedule.schedule_id
        })

    for day, day_schedules in routine_data.items():
        day_schedules.sort(key=lambda x: x['start_time'])

    day_order = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    ordered_routine_data = []
    for day in day_order:
        if day in routine_data:
            ordered_routine_data.append(routine_data[day])

    # Get all classes and teachers for filter options
    classes = Class.query.all()
    teachers = User.query.filter(User.role.in_(['Assistant Teacher', 'Admin', 'Assistant Head Teacher'])).all()  # Filter for teachers and admins

    return render_template('show_routine.html',
                           routine_data=ordered_routine_data,
                           selected_day=selected_day,
                           user_role=user_role,
                           classes=classes,
                           teachers=teachers,
                           selected_class=selected_class,
                           selected_teacher=selected_teacher,
                           schedules=schedules)
@app.route('/admin_dashboard')
def admin_dashboard():
    if not (session.get('logged_in') and session.get('user_role') == 'Admin'):
        return redirect(url_for('app.login'))

    user = User.query.filter_by(user_id=session.get('user_id')).first()
    num_of_users = User.query.count()
    designation = 'Head Master' if user.phone =='01712521742' else 'Admin'

    # Get Dhaka time
    dhaka_timezone = pytz.timezone("Asia/Dhaka")
    now_dhaka = datetime.now(dhaka_timezone)

    # Get all currently running classes
    running_classes = []
    for schedule in TeacherSchedule.query.all():
        start_time = datetime.combine(now_dhaka.date(), schedule.start_time).replace(tzinfo=dhaka_timezone)
        end_time = datetime.combine(now_dhaka.date(), schedule.end_time).replace(tzinfo=dhaka_timezone)

    # Check if the class is TODAY and within the current time
        if schedule.day_of_week == now_dhaka.strftime('%A') and start_time <= now_dhaka <= end_time: 
            teacher = User.query.get(schedule.teacher_id)
            class_ = Class.query.get(schedule.class_id)
            subject = Subject.query.get(schedule.subject_id)
            running_classes.append({
                'teacher': teacher.name,
                'class': class_.class_name,
                'subject': subject.subject_name,
                'section': class_.section
            })
    # Get today's classes
    todays_classes = []
    for schedule in TeacherSchedule.query.all():
        if schedule.day_of_week == now_dhaka.strftime('%A'):
            teacher = User.query.get(schedule.teacher_id)
            class_ = Class.query.get(schedule.class_id)
            subject = Subject.query.get(schedule.subject_id)
            todays_classes.append({
                'teacher': teacher.name,
                'class': class_.class_name,
                'subject': subject.subject_name,
                'section': class_.section,
                'start_time': schedule.start_time.strftime('%I:%M %p'),
                'end_time': schedule.end_time.strftime('%I:%M %p')
            })

    if not todays_classes:
        todays_classes = "No classes today"

    if not running_classes:
        running_classes = "No classes running now"

    # Get number of teachers
    num_of_teachers = User.query.filter(User.role.in_(['Admin','Assistant Teacher', 'Assistant Head Teacher'])).count()

    # Get all news
    all_news = News.query.all()

    return render_template(
        'admin_dashboard.html',
        name=user.name,
        num_of_users=num_of_users,
        num_of_teachers=num_of_teachers,
        running_classes=running_classes,
        todays_classes=todays_classes,
        all_news=all_news,designation = designation
    )


@app.route('/admin/create_routine', methods=['GET', 'POST'])
def create_routine():
    if not (session.get('logged_in') and session.get('user_role') == 'Admin'):
        return redirect(url_for('app.login'))  # Redirect to login if not logged in as admin

    form = TeacherScheduleForm()

    # Populate form choices dynamically
    form.teacher.choices = [(teacher.user_id, teacher.name) for teacher in
                            User.query.filter(User.role.in_(['Assistant Teacher', 'Admin', 'Assistant Head Teacher'])).all()]

    form.class_.choices = [(class_.class_id, class_.class_name) for class_ in Class.query.all()]
    form.subject.choices = [(subject.subject_id, subject.subject_name) for subject in Subject.query.all()]

    if form.validate_on_submit():
        for day in form.day_of_week.data:  # Iterate over selected days
            schedule = TeacherSchedule(
                teacher_id=form.teacher.data,
                class_id=form.class_.data,
                subject_id=form.subject.data,
                day_of_week=day,  # Use the individual day here
                start_time=form.start_time.data,
                end_time=form.end_time.data
            )
            db.session.add(schedule)
        db.session.commit()
        flash('Schedule created successfully!', 'success')
        return redirect(url_for('app.create_routine'))  # Redirect to the same page after successful creation

    return render_template('create_routine.html', form=form)
@app.route('/admin/update_routine/<int:schedule_id>', methods=['GET', 'POST'])
def update_routine(schedule_id):
    if not (session.get('logged_in') and session.get('user_role') == 'Admin'):
        return redirect(url_for('app.login'))

    schedule = TeacherSchedule.query.get_or_404(schedule_id)
    form = TeacherScheduleForm(obj=schedule)  # Pre-populate the form with existing data

    form.teacher.choices = [(teacher.user_id, teacher.name) for teacher in
                            User.query.filter(User.role.in_(['Assistant Teacher', 'Admin', 'Assistant Head Teacher'])).all()]
    form.class_.choices = [(class_.class_id, class_.class_name) for class_ in Class.query.all()]
    form.subject.choices = [(subject.subject_id, subject.subject_name) for subject in Subject.query.all()]

    if form.validate_on_submit():
        schedule.teacher_id = form.teacher.data
        schedule.class_id = form.class_.data
        schedule.subject_id = form.subject.data
        # Assuming day_of_week remains the same, otherwise handle it accordingly
        schedule.start_time = form.start_time.data
        schedule.end_time = form.end_time.data
        db.session.commit()
        flash('Schedule updated successfully!', 'success')
        return redirect(url_for('app.show_routine'))  # Redirect to the routine page

    return render_template('update_routine.html', form=form, schedule=schedule)

@app.route('/admin/add_user', methods=["GET", "POST"])
def add_user():
    if not (session.get('logged_in') and session.get('user_role') == 'Admin'):
        return redirect(url_for('app.login'))
    form = AddUserForm()

    if form.validate_on_submit():  # Move this check to the beginning
        name = form.name.data
        phone = form.phone.data
        role = form.role.data

        new_user = User(name=name, phone=phone, role=role)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash("User added successfully!", "success")
            return redirect(url_for('app.admin_dashboard'))  # Redirect to admin dashboard
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding user: {e}", "danger")
    return render_template('add_user.html',form=form)

@app.route('/news', methods=['GET', 'POST'])
def news():
    if not (session.get('logged_in') and session.get('user_role')):
        return redirect(url_for('app.login'))

    form = NewsForm()
    if form.validate_on_submit():
        # Process links, bolding, and anchors in the content
        content_with_html = process_content(form.content.data)

        news_item = News(
            title=form.title.data,
            content=content_with_html, 
            created_by=session.get('user_id')
        )
        db.session.add(news_item)
        db.session.commit()
        flash('News created successfully!', 'success')
        return redirect(url_for('app.news'))

    show_all = request.args.get('show_all', False) 

    if show_all:
        all_news = News.query.all()
    else:
        today = datetime.utcnow().date()
        all_news = News.query.filter(db.func.date(News.created_at) == today).all()

    return render_template('news.html', form=form, all_news=all_news, user_role=session.get('user_role'))

@app.route('/delete_news/<int:news_id>', methods=['POST']) 
def delete_news(news_id):
    if not (session.get('logged_in') and session.get('user_role') == 'Admin'):
        return redirect(url_for('app.login'))  # Or another appropriate response

    news_item = News.query.get_or_404(news_id)
    db.session.delete(news_item)
    db.session.commit()
    flash('News item deleted!', 'success')
    return redirect(url_for('app.news'))

def process_content(content):
    # Find and replace links with <a> tags
    content = re.sub(r'(https?://[^\s]+)', r'<a href="\1" target="_blank">\1</a>', content)

    # Find and replace bold text with <strong> tags
    content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)

    # Find and replace anchors with <a> tags (e.g., [Link Text](#anchor))
    content = re.sub(r'\[(.+?)\]\((#.+?)\)', r'<a href="\2">\1</a>', content)

    return content


    # Fetch all news items (you might want to paginate this later)
    all_news = News.query.all()
    return render_template('news.html', form=form, all_news=all_news,user_role=session.get('user_role'))


@app.route('/user_dashboard')
def user_dashboard():
    if not (session.get('logged_in') and session.get('user_role') in ('Assistant Teacher', 'Assistant Head Teacher')):
        return redirect(url_for('app.login'))

    user = User.query.filter_by(user_id=session.get('user_id')).first()
    latest_news = News.query.order_by(News.news_id.desc()).first()

    # Get Dhaka time
    dhaka_timezone = pytz.timezone("Asia/Dhaka")
    now_dhaka = datetime.now(dhaka_timezone)

    # Get today's schedule for the logged-in teacher
    todays_schedule = TeacherSchedule.query.filter_by(teacher_id=user.user_id).all()
   
     

    # Filter for today's classes based on Dhaka time
    todays_classes = []
    current_class = None
    remaining_time = None
    for schedule in todays_schedule:
        start_time = datetime.combine(now_dhaka.date(), schedule.start_time).replace(tzinfo=dhaka_timezone)
        end_time = datetime.combine(now_dhaka.date(), schedule.end_time).replace(tzinfo=dhaka_timezone)

        # Check if the class is TODAY and within the current time
        if schedule.day_of_week == now_dhaka.strftime('%A'): 
        	class_info = {
            	'class': Class.query.get(schedule.class_id).class_name,
            	'subject': Subject.query.get(schedule.subject_id).subject_name,
            	'section': Class.query.get(schedule.class_id).section,
            	'start_time': schedule.start_time.strftime('%I:%M %p'),
            	'end_time': schedule.end_time.strftime('%I:%M %p')
        		}
        
        	todays_classes.append(class_info)

        # Check if this is the current class
        if start_time <= now_dhaka <= end_time:
            current_class = class_info
            remaining_time = end_time - now_dhaka
            remaining_time = str(timedelta(seconds=remaining_time.seconds))

    if not todays_classes:
        todays_classes = "No classes today"

    return render_template(
        'user_dashboard.html',
        name=user.name,
        designation=user.role,
        todays_classes=todays_classes,
        current_class=current_class,  # Pass the current_class dictionary
        remaining_time=remaining_time,
        latest_news=latest_news
    )
