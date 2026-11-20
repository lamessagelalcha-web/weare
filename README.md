# OEMS — Online Examination Management System

A starter web application for managing exams with Admin, Teacher, and Student roles. This project is intentionally supplied as a normal source folder (not a ZIP archive).

## Included
- Username/password login and role-based dashboards
- Admin creates Teacher and Student accounts, resets passwords, and disables/enables users
- Teacher/Admin creates exams, sets duration and optional availability window, adds multiple-choice questions, and publishes/unpublishes exams
- PDF text import using the format below
- Student timed exam page and submission
- Automatic grading for A/B/C/D multiple-choice questions
- Teacher/Admin result lists
- SQLite for local development; PostgreSQL via `DATABASE_URL` for hosting

## Important limitations before production
This is an MVP learning/development project, not a high-stakes secure testing product. Before real exams, add and test CSRF protection, server-side exam timing enforcement, robust rate limits, audit logs, backup/restore, question import review, privacy controls, and stronger anti-cheating/identity processes. Browser countdown is not a security boundary. The current PDF importer handles selectable-text PDFs only and does not OCR scans. Exam scoring is automatic only for multiple-choice questions. Admin accounts must be provisioned securely; avoid leaving default credentials active.

## 1. Install prerequisites
Install:
- Python 3.11 or newer
- Git
- VS Code (recommended)
- A GitHub account

Check installation in a terminal:
```bash
python --version
git --version
```

## 2. Open the project
Open this `OEMS` folder in VS Code. Open VS Code Terminal: **Terminal → New Terminal**.

## 3. Create a virtual environment
Windows PowerShell:
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```
If PowerShell blocks activation, you can use Command Prompt instead:
```bat
.venv\Scripts\activate.bat
```
macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 4. Install Python packages
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 5. Configure local administrator
Copy `.env.example` to `.env` (in VS Code: right-click copy/paste and rename). Edit `.env` and set your own admin username and strong password. Example:
```env
SECRET_KEY=make-a-long-random-secret-string
DATABASE_URL=
ADMIN_USERNAME=admin
ADMIN_PASSWORD=ReplaceWithAUniquePassword123!
ADMIN_NAME=System Administrator
FLASK_DEBUG=true
```
Do not upload `.env` to GitHub. `.gitignore` prevents it from being tracked.

## 6. Run locally
```bash
python app.py
```
Open your browser at:
- http://127.0.0.1:5000

Login using the admin username/password set in `.env`. If you edit the admin password after the first admin record was created, use the Admin dashboard to reset a non-admin user; change an admin password directly through a secure database/admin process. For a fresh local database, delete `instance/oems.db` only if you intentionally want to reset local data, then restart.


## 7. Admin workflow
1. Sign in as Admin.
2. Create Teacher and Student accounts. Passwords must have at least 8 characters.
3. Teachers can sign in and create exams.
4. Admin can also create exams.
5. Use the dashboard to manage users, toggle account access, and reset non-admin passwords.

## 8. Teacher workflow
1. Sign in.
2. Select **Create Exam**.
3. Enter exam title, subject, duration, and optional start/end schedule.
4. Add questions manually, or import PDF questions.
5. Review imported questions and answer keys.
6. Publish the exam. Students see published exams within the schedule window.
7. View **Results** to see student submissions.

## 9. Student workflow
1. Sign in with the student account given by the school.
2. Open an available exam.
3. Answer the questions.
4. Submit before the timer expires.
5. View the result page.


## 10. PDF question import format
The PDF must contain selectable text. Each question should use this structure. Ensure a question starts on a new numbered line. Four choices and an answer key are required.


```text
1. Which component is called the brain of a computer?
A) Monitor
B) CPU
C) Keyboard
D) Mouse
Answer: B

2. Which of the following is an input device?
A) Printer
B) Speaker
C) Keyboard
D) Projector
Answer: C
```

The importer detects numbered questions, options A–D, and `Answer: A/B/C/D` (also `Correct: A`). The PDF should not be a scan/image-only file. After import, inspect the question list and answer keys before publishing. PDF import assigns one point to each imported question.

## 11. Git setup and GitHub deployment

### A. Initialize Git locally
In the project folder terminal:
```bash
git init
git add .
git commit -m "Initial OEMS project"
```

### B. Create a GitHub repository
1. Sign in to GitHub.
2. Click **New repository**.
3. Name it `OEMS` (or another name).
4. Set visibility as you prefer. For a school project, private is recommended if it contains any non-public data. Never commit student records, passwords, or real exam papers.
5. Create the repository without adding another README (this project already has one).

### C. Connect and push
Replace `YOUR-USERNAME` and `YOUR-REPOSITORY` with your repository details:
```bash
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin main
```
If `origin` already exists, check it:
```bash
git remote -v
```
Update it if necessary:
```bash
git remote set-url origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin main
```

## 12. Deploy on Render
Render is one hosting option for this Flask app. Platform screens may change, so follow their current UI labels.

1. Create/sign in to a Render account.
2. Create a managed **PostgreSQL** database. Copy/attach its internal connection string as `DATABASE_URL` for the web service (Render Blueprint can provision both using `render.yaml`).
3. In Render, choose **New → Blueprint** and connect your GitHub OEMS repository. Render reads `render.yaml` and creates the web service and database. Alternatively, create a Web Service from the repository and set:
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app`
4. Add environment variables in the Render service settings:
   - `SECRET_KEY`: long random secret (Render may generate it from Blueprint)
   - `ADMIN_USERNAME`: secure initial administrator username
   - `ADMIN_PASSWORD`: a strong unique password (set as secret)
   - `ADMIN_NAME`: administrator display name
   - `DATABASE_URL`: your PostgreSQL connection string (Render Blueprint can link it)
5. Deploy. Wait for the build and service to finish.
6. Open the generated Render URL. Test login, create teacher/student accounts, create an exam, add sample questions, publish, take it using a test student, and check the results.
7. Store the live URL securely and never use test accounts/passwords for real users.

## 13. Update website after changes
Whenever you edit files locally and want to update the live site:
```bash
git add .
git commit -m "Describe your update"
git push
```
If automatic deploy is enabled, Render will redeploy after the push.

## 14. Troubleshooting
- **Python command not found:** install Python, reopen terminal, and try `py --version` on Windows or `python3 --version` on macOS/Linux.
- **Virtual environment not active:** run the activation command for your terminal.
- **Missing module:** activate the venv and run `pip install -r requirements.txt`.
- **Database connection error:** check `DATABASE_URL` and verify the PostgreSQL service is available. For local development, leave it blank to use SQLite.
- **PDF import shows 0:** the PDF may be scanned, text extraction may be out of order, or the question format may not match. Try a selectable-text PDF with the template above.
- **Git push rejected:** use `git pull --rebase origin main` only after reviewing remote changes; resolve conflicts, then push.
- **Exam does not appear for students:** check the exam is published, has questions, and the optional start/end times are correct.

## 15. File overview
- `app.py`: routes, login, exam flow, PDF parsing, scoring
- `models.py`: database tables
- `config.py`: app settings
- `templates/`: HTML pages
- `static/css/style.css`: styling
- `static/js/exam_timer.js`: exam countdown UI
- `requirements.txt`: dependencies
- `render.yaml`: deployment Blueprint configuration
- `Procfile`: Gunicorn start command
- `.env.example`: environment variable template

## Project license
Choose and add a license before public reuse. Do not include real student personal information in sample data or repositories.
#   w e a r e  
 