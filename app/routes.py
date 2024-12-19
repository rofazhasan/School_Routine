from flask import Blueprint, request, render_template, flash, redirect, url_for, session
from app.models import User,Class ,Subject,TeacherSchedule,News
from app.forms import LoginForm, AddUserForm,NewsForm,ChangePasswordForm,TeacherScheduleForm
from app.database import db
from datetime import datetime, time, timedelta,timezone
import pytz



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
        return redirect(url_for('app.login'))

    user_id = session.get('user_id')
    user_role = session.get('user_role')

    if request.method == 'POST':
        selected_day = request.form.get('day_of_week')
    else:
        selected_day = None  # No day selected by default

    if user_role == 'Admin':
        # Admin view: Show all schedules
        schedules = TeacherSchedule.query
    else:
        # User view: Show only their schedules
        schedules = TeacherSchedule.query.filter_by(teacher_id=user_id)
        if selected_day:
            schedules = schedules.filter_by(day_of_week=selected_day)
        schedules = schedules.all()

    # Prepare data for the template
    routine_data = []
    for schedule in schedules:
        teacher = User.query.get(schedule.teacher_id)
        class_ = Class.query.get(schedule.class_id)
        subject = Subject.query.get(schedule.subject_id)
        routine_data.append({
            'teacher': teacher.name,
            'class': class_.class_name,
            'subject': subject.subject_name,
            'day': schedule.day_of_week,
            'start_time': schedule.start_time.strftime('%I:%M %p'),
            'end_time': schedule.end_time.strftime('%I:%M %p')
        })

    return render_template('show_routine.html', routine_data=routine_data, selected_day=selected_day, user_role=user_role)
@app.route('/admin_dashboard')
def admin_dashboard():
    if not (session.get('logged_in') and session.get('user_role') == 'Admin'):
        return redirect(url_for('app.login'))

    user = User.query.filter_by(user_id=session.get('user_id')).first()
    num_of_users = User.query.count()
    if user.phone=='01712521742':
        designation = 'Head Master'

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
    num_of_teachers = User.query.filter(User.role.in_(['Assistant Teacher', 'Assistant Head Teacher'])).count()

    # Get all news
    all_news = News.query.all()

    return render_template(
        'admin_dashboard.html',
        name=user.name,
        num_of_users=num_of_users,
        num_of_teachers=num_of_teachers,
        running_classes=running_classes,
        todays_classes=todays_classes,
        all_news=all_news,designation = designation else 'Admin'
    )


@app.route('/admin/create_routine', methods=['GET', 'POST'])
def create_routine():
    if not (session.get('logged_in') and session.get('user_role') == 'Admin'):
        return redirect(url_for('app.login'))  # Redirect to login if not logged in as admin

    form = TeacherScheduleForm()

    # Populate form choices dynamically
    form.teacher.choices = [(teacher.user_id, teacher.name) for teacher in
                            User.query.filter_by(role='Assistant Teacher').all()]
    form.class_.choices = [(class_.class_id, class_.class_name) for class_ in Class.query.all()]
    form.subject.choices = [(subject.subject_id, subject.subject_name) for subject in Subject.query.all()]

    if form.validate_on_submit():
        schedule = TeacherSchedule(
            teacher_id=form.teacher.data,
            class_id=form.class_.data,
            subject_id=form.subject.data,
            day_of_week=form.day_of_week.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data
        )
        db.session.add(schedule)
        db.session.commit()
        flash('Schedule created successfully!', 'success')
        return redirect(url_for('app.create_routine'))  # Redirect to the same page after successful creation

    return render_template('create_routine.html', form=form)


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

@app.route('/admin/news', methods=["GET", "POST"])
def news():
    if not (session.get('logged_in') and session.get('user_role')):
        return redirect(url_for('app.login'))

    form = NewsForm()
    if form.validate_on_submit():
        news_item = News(
            title=form.title.data,
            content=form.content.data,
            created_by=session.get('user_id')  # Get the logged-in admin's ID
        )
        db.session.add(news_item)
        db.session.commit()
        flash('News created successfully!', 'success')
        return redirect(url_for('app.news'))  # Redirect to the news page

    # Fetch all news items (you might want to paginate this later)
    all_news = News.query.all()
    return render_template('news.html', form=form, all_news=all_news)


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
        if schedule.day_of_week == now_dhaka.strftime('%A') and start_time <= now_dhaka <= end_time:
            current_class = {  # Store current class details in a dictionary
                'class': Class.query.get(schedule.class_id).class_name,
                'subject': Subject.query.get(schedule.subject_id).subject_name,
                'section': Class.query.get(schedule.class_id).section,
                'start_time': schedule.start_time.strftime('%I:%M %p'),
                'end_time': schedule.end_time.strftime('%I:%M %p')
            }
            remaining_time = end_time - now_dhaka
            remaining_time = str(timedelta(seconds=remaining_time.seconds))  # Format remaining time

            todays_classes.append(current_class)  # Add current class to today's classes

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
