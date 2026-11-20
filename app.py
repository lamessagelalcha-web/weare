import os, re
from dotenv import load_dotenv
load_dotenv()
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from pypdf import PdfReader
from config import Config
from models import db, User, Exam, Question, Submission, Answer


app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def role_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                abort(403)
            return fn(*args, **kwargs)
        return wrapped
    return decorator


def exam_available(exam):
    now = datetime.utcnow()
    return exam.published and (not exam.start_at or now >= exam.start_at) and (not exam.end_at or now <= exam.end_at)


def parse_pdf_questions(text):
    # Supported layout: question text; A) option; B) option; C) option; D) option; Answer: B
    blocks = re.split(r'(?m)(?=^\s*\d+[.)]\s+)', text.strip())
    parsed = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        qline = re.sub(r'^\d+[.)]\s*', '', lines[0])
        opts = {}
        answer = None
        for line in lines[1:]:
            match = re.match(r'^([A-D])[.)]\s*(.+)$', line, re.I)
            if match:
                opts[match.group(1).upper()] = match.group(2).strip()
            ans = re.search(r'(?:answer|correct)\s*[:\-]\s*([A-D])\b', line, re.I)
            if ans:
                answer = ans.group(1).upper()
        if qline and all(k in opts for k in 'ABCD') and answer:
            parsed.append({'text': qline, 'options': opts, 'correct': answer})
    return parsed


@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username','').strip()).first()
        if user and user.active and check_password_hash(user.password_hash, request.form.get('password','')):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Username or password is incorrect.', 'danger')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        users = User.query.order_by(User.role, User.username).all()
        exams = Exam.query.order_by(Exam.id.desc()).all()
        return render_template('admin/dashboard.html', users=users, exams=exams)
    if current_user.role == 'teacher':
        exams = Exam.query.filter_by(teacher_id=current_user.id).order_by(Exam.id.desc()).all()
        return render_template('teacher/dashboard.html', exams=exams)
    exams = Exam.query.filter_by(published=True).order_by(Exam.id.desc()).all()
    exams = [e for e in exams if exam_available(e)]
    submitted_ids = {s.exam_id for s in Submission.query.filter_by(student_id=current_user.id).all()}
    return render_template('student/dashboard.html', exams=exams, submitted_ids=submitted_ids)


@app.route('/admin/users', methods=['POST'])
@login_required
@role_required('admin')
def create_user():
    username = request.form.get('username','').strip()
    full_name = request.form.get('full_name','').strip()
    password = request.form.get('password','')
    role = request.form.get('role','student')
    if role not in ('teacher','student') or not username or not full_name or len(password) < 8:
        flash('Please fill all fields. Password must be at least 8 characters.', 'warning')
    elif User.query.filter_by(username=username).first():
        flash('That username already exists.', 'warning')
    else:
        db.session.add(User(username=username, full_name=full_name, password_hash=generate_password_hash(password), role=role))
        db.session.commit()
        flash('Account created.', 'success')
    return redirect(url_for('dashboard'))


@app.route('/admin/users/<int:user_id>/reset', methods=['POST'])
@login_required
@role_required('admin')
def reset_user_password(user_id):
    user = User.query.get_or_404(user_id)
    password = request.form.get('new_password','')
    if user.role == 'admin' or len(password) < 8:
        flash('Admin password reset is not available here. Use at least 8 characters.', 'warning')
    else:
        user.password_hash = generate_password_hash(password)
        db.session.commit()
        flash('Password updated.', 'success')
    return redirect(url_for('dashboard'))


@app.route('/admin/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@role_required('admin')
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role != 'admin':
        user.active = not user.active
        db.session.commit()
    return redirect(url_for('dashboard'))


@app.route('/exams/create', methods=['GET','POST'])
@login_required
@role_required('admin','teacher')
def create_exam():
    if request.method == 'POST':
        try:
            duration = max(1, min(int(request.form.get('duration', 30)), 360))
            start = datetime.fromisoformat(request.form['start_at']) if request.form.get('start_at') else None
            end = datetime.fromisoformat(request.form['end_at']) if request.form.get('end_at') else None
        except ValueError:
            flash('Check duration and date values.', 'danger')
            return redirect(url_for('create_exam'))
        exam = Exam(title=request.form.get('title','').strip(), subject=request.form.get('subject','').strip(), description=request.form.get('description',''), duration_minutes=duration, start_at=start, end_at=end, published=False, teacher_id=current_user.id)
        if not exam.title or not exam.subject:
            flash('Exam title and subject are required.', 'warning')
        else:
            db.session.add(exam); db.session.commit()
            flash('Exam created. Add questions before publishing.', 'success')
            return redirect(url_for('manage_exam', exam_id=exam.id))
    return render_template('exam_create.html')


@app.route('/exams/<int:exam_id>/manage', methods=['GET','POST'])
@login_required
@role_required('admin','teacher')
def manage_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    if current_user.role == 'teacher' and exam.teacher_id != current_user.id:
        abort(403)
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'publish':
            if not exam.questions:
                flash('Add at least one question before publishing.', 'warning')
            else:
                exam.published = True; db.session.commit(); flash('Exam published.', 'success')
        elif action == 'unpublish':
            exam.published = False; db.session.commit(); flash('Exam unpublished.', 'info')
        elif action == 'add_question':
            q = Question(exam_id=exam.id, text=request.form.get('question','').strip(), option_a=request.form.get('a','').strip(), option_b=request.form.get('b','').strip(), option_c=request.form.get('c','').strip(), option_d=request.form.get('d','').strip(), correct=request.form.get('correct','A'), points=max(1, int(request.form.get('points',1))))
            if not q.text or not all([q.option_a,q.option_b,q.option_c,q.option_d]) or q.correct not in 'ABCD':
                flash('Question and all four options are required.', 'warning')
            else:
                db.session.add(q); db.session.commit(); flash('Question added.', 'success')
        elif action == 'import_pdf':
            file = request.files.get('pdf')
            if not file or not file.filename.lower().endswith('.pdf'):
                flash('Choose a PDF file.', 'warning')
            else:
                try:
                    reader = PdfReader(file)
                    text = '\n'.join(page.extract_text() or '' for page in reader.pages)
                    qs = parse_pdf_questions(text)
                    for item in qs:
                        db.session.add(Question(exam_id=exam.id, text=item['text'], option_a=item['options']['A'], option_b=item['options']['B'], option_c=item['options']['C'], option_d=item['options']['D'], correct=item['correct'], points=1))
                    db.session.commit()
                    flash(f'Imported {len(qs)} question(s). Review the imported questions before publishing.', 'success' if qs else 'warning')
                except Exception as exc:
                    flash('Could not read PDF. Ensure it contains selectable text and matches the template.', 'danger')
        return redirect(url_for('manage_exam', exam_id=exam.id))
    return render_template('exam_manage.html', exam=exam)


@app.route('/exams/<int:exam_id>/delete-question/<int:question_id>', methods=['POST'])
@login_required
@role_required('admin','teacher')
def delete_question(exam_id, question_id):
    exam = Exam.query.get_or_404(exam_id)
    if current_user.role == 'teacher' and exam.teacher_id != current_user.id: abort(403)
    q = Question.query.filter_by(id=question_id, exam_id=exam_id).first_or_404()
    db.session.delete(q); db.session.commit(); flash('Question removed.', 'info')
    return redirect(url_for('manage_exam', exam_id=exam.id))


@app.route('/exams/<int:exam_id>/take', methods=['GET','POST'])
@login_required
@role_required('student')
def take_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    if not exam_available(exam): abort(403)
    if Submission.query.filter_by(exam_id=exam.id, student_id=current_user.id).first():
        flash('You already submitted this exam.', 'info'); return redirect(url_for('dashboard'))
    questions = exam.questions
    if request.method == 'POST':
        submission = Submission(exam_id=exam.id, student_id=current_user.id, max_score=sum(q.points for q in questions))
        db.session.add(submission); db.session.flush()
        score = 0
        for q in questions:
            selected = request.form.get(f'q_{q.id}', '')
            db.session.add(Answer(submission_id=submission.id, question_id=q.id, selected=selected if selected in 'ABCD' else None))
            if selected == q.correct: score += q.points
        submission.score = score; db.session.commit()
        flash('Exam submitted successfully.', 'success'); return redirect(url_for('my_result', submission_id=submission.id))
    return render_template('student/take_exam.html', exam=exam, questions=questions)


@app.route('/results/<int:submission_id>')
@login_required
def my_result(submission_id):
    sub = Submission.query.get_or_404(submission_id)
    if current_user.role == 'student' and sub.student_id != current_user.id: abort(403)
    if current_user.role == 'teacher' and sub.exam.teacher_id != current_user.id: abort(403)
    return render_template('result.html', sub=sub)


@app.route('/results')
@login_required
@role_required('admin','teacher')
def results():
    if current_user.role == 'teacher':
        exam_ids = [e.id for e in Exam.query.filter_by(teacher_id=current_user.id).all()]
        subs = Submission.query.filter(Submission.exam_id.in_(exam_ids)).order_by(Submission.submitted_at.desc()).all() if exam_ids else []
    else:
        subs = Submission.query.order_by(Submission.submitted_at.desc()).all()
    return render_template('results.html', submissions=subs)


@app.route('/health')
def health():
    return {'status':'ok'}


with app.app_context():
    db.create_all()
    admin_username = os.environ.get('ADMIN_USERNAME')
    admin_password = os.environ.get('ADMIN_PASSWORD')
    if admin_username and admin_password and not User.query.filter_by(username=admin_username).first():
        db.session.add(User(username=admin_username, full_name=os.environ.get('ADMIN_NAME','System Administrator'), password_hash=generate_password_hash(admin_password), role='admin'))
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG','false').lower() == 'true')
