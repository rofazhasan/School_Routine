from flask_sqlalchemy import SQLAlchemy
from database import db
from datetime import datetime

# Users Table
class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.Enum('Admin', 'Assistant Head Teacher', 'Assistant Teacher', name='user_roles'), nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False, default='123456')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Classes Table
class Class(db.Model):
    __tablename__ = 'classes'
    class_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    class_name = db.Column(db.String(50), nullable=False)
    section = db.Column(db.String(10), nullable=True)

# Subjects Table
class Subject(db.Model):
    __tablename__ = 'subjects'
    subject_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    subject_name = db.Column(db.String(100), nullable=False)

# Teacher Schedule Table
class TeacherSchedule(db.Model):
    __tablename__ = 'teacher_schedules'
    schedule_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.class_id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.subject_id'), nullable=False)
    day_of_week = db.Column(db.Enum('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday', name='days_of_week'), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    teacher = db.relationship('User', backref='schedules')
    classroom = db.relationship('Class', backref='schedules')
    subject = db.relationship('Subject', backref='schedules')

# News Table
class News(db.Model):
    __tablename__ = 'news'
    news_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    admin = db.relationship('User', backref='news_created')
