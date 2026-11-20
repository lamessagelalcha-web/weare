from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    full_name = db.Column(db.String(140), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, teacher, student
    active = db.Column(db.Boolean, default=True, nullable=False)

class Exam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    subject = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, default='')
    duration_minutes = db.Column(db.Integer, default=30, nullable=False)
    start_at = db.Column(db.DateTime, nullable=True)
    end_at = db.Column(db.DateTime, nullable=True)
    published = db.Column(db.Boolean, default=False, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    questions = db.relationship('Question', backref='exam', cascade='all, delete-orphan')


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.Text, nullable=False)
    option_b = db.Column(db.Text, nullable=False)
    option_c = db.Column(db.Text, nullable=False)
    option_d = db.Column(db.Text, nullable=False)
    correct = db.Column(db.String(1), nullable=False)
    points = db.Column(db.Integer, default=1, nullable=False)

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    score = db.Column(db.Integer, default=0, nullable=False)
    max_score = db.Column(db.Integer, default=0, nullable=False)
    exam = db.relationship('Exam')
    student = db.relationship('User')
    answers = db.relationship('Answer', backref='submission', cascade='all, delete-orphan')
    __table_args__ = (db.UniqueConstraint('exam_id', 'student_id', name='unique_exam_student'),)


class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submission.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    selected = db.Column(db.String(1), nullable=True)
