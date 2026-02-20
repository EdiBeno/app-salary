# -----------------------------
from uuid import uuid4
import os, csv, json, logging, calendar, re, secrets
from dotenv import load_dotenv
from functools import wraps
from flask_login import LoginManager, login_user, logout_user, login_required as flask_login_required, current_user
from flask import Flask, render_template, request, redirect, url_for, jsonify, Response, session, flash
from flask_session import Session
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import disconnect
from flask_socketio import SocketIO, emit
from flask_mail import Mail, Message
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy import Text
import time
from datetime import datetime, timedelta, timezone
import pandas as pd
import numpy as np
import openpyxl, xlsxwriter

# -----------------------------
# Models & Logic 
# -----------------------------
from database import db, EmployeeData, MonthlyRecord, HoursData, PasswordResetToken, CustomerForm, TaxCredit, BankAccount , Invoice , Product, Timesheet, User
from data import get_employees, add_employee

# -----------------------------
# Init .env + Flask 
# -----------------------------
load_dotenv()
app = Flask(__name__, static_folder="static")

# Correct SocketIO init
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

@socketio.on('connect')
def handle_connect():
    print("✅ A client connected via Socket.IO")
    emit('connected', {'msg': 'Welcome! You are connected to the server.'})

# ----------------------
# Getting Import Time Processor
# ----------------------
@app.context_processor
def inject_time():
    return dict(time=time)

# -----------------------------
# Secret Key
# -----------------------------
app.secret_key = os.getenv("SECRET_KEY") or secrets.token_hex(32)

# -----------------------------
# Database Config (multi-option)
# -----------------------------
db_choice = os.getenv("DB_CHOICE", "sqlite").lower()

if db_choice == "postgres":
    uri = os.getenv("POSTGRES_URI")
    # תיקון קריטי: Render/Heroku שולחים postgres:// אבל SQLAlchemy 2.0 דורש postgresql://
    if uri and uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = uri
elif db_choice == "mysql":
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("MYSQL_URI")
elif db_choice == "mssql":
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("MSSQL_URI")
else:
    # Default to SQLite
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLITE_URI", "sqlite:///data.db")

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# -----------------------------
# Session Config
# -----------------------------
app.config['SESSION_TYPE'] = 'filesystem'
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=60)

# -----------------------------
# Mail Config
# -----------------------------
app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.office365.com")
app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")

# -----------------------------
# JWT Config
# -----------------------------
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", secrets.token_hex(32))

# -----------------------------
# Init Extensions
# -----------------------------
db.init_app(app)
Session(app)
migrate = Migrate(app, db)
mail = Mail(app)
jwt = JWTManager(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -----------------------------
# Create Tables (Safe context)
# -----------------------------
with app.app_context():
    try:
        db.create_all()
        print(f"✅ Database initialized on: {db_choice}")
    except Exception as e:
        print(f"❌ Error initializing Database: {e}")

# -----------------------------
# Owner Credentials
# -----------------------------
OWNER_USERNAME = os.getenv("OWNER_USERNAME")
OWNER_PASSWORD = generate_password_hash(os.getenv("OWNER_PASSWORD"))

# -----------------------------
# Decorators
# -----------------------------

def OWNER_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('owner_access'):
            flash('⛔ אין לך הרשאה לגשת לעמוד הזה (רק בעלים)', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Owner OR logged-in SQL user
        if not session.get('owner_access') and not session.get('user_id'):
            flash("⛔ אין גישה — התחבר קודם", "danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# Manager only
def manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        # OWNER ALWAYS ALLOWED
        if session.get('owner_access'):
            return f(*args, **kwargs)

        if session.get('role') != 'manager':
            flash("⛔ אין לך הרשאה (מנהל בלבד)", "danger")
            return redirect(url_for('unauthorized'))
        return f(*args, **kwargs)
    return decorated_function


# Employee only
def employee_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        # OWNER ALWAYS ALLOWED
        if session.get('owner_access'):
            return f(*args, **kwargs)

        if session.get('role') != 'employee':
            flash("⛔ רק עובדים יכולים להיכנס לדף זה", "danger")
            return redirect(url_for('unauthorized'))
        return f(*args, **kwargs)
    return decorated_function


# Employee can ONLY view himself
def employee_self_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        # OWNER ALWAYS ALLOWED
        if session.get('owner_access'):
            return f(*args, **kwargs)

        selected_employee_id = (
            kwargs.get('employee_id') or
            request.args.get('employee_id')
        )

        if session.get('role') == 'employee':
            if str(session.get('employee_id')) != str(selected_employee_id):
                flash("⛔ אין לך הרשאה לראות עובד אחר", "danger")
                return redirect(url_for('unauthorized'))

        return f(*args, **kwargs)
    return decorated_function


# Employee OR Manager
def employee_or_manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        # OWNER ALWAYS ALLOWED
        if session.get('owner_access'):
            return f(*args, **kwargs)

        if session.get('role') not in ['employee', 'manager']:
            flash("⛔ אין לך הרשאה", "danger")
            return redirect(url_for('unauthorized'))

        return f(*args, **kwargs)
    return decorated_function


# Unauthorized page
@app.route('/unauthorized')
def unauthorized():
    role = session.get('role')

    # OWNER
    if session.get('owner_access'):
        return redirect('/index')

    # MANAGER
    if role == 'manager':
        return redirect('/index')

    # EMPLOYEE
    if role == 'employee':
        return redirect('/employee_dashboard')

    # OTHER
    return "<h1>⛔ אין לך הרשאה</h1>", 403


# -----------------------------
# Login Route
# -----------------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        session.clear()
        return render_template('login.html')

    role = request.form.get('role')

    if role == "employee":
        email = request.form.get('employee_email', '').strip()
    else:
        email = request.form.get('email', '').strip()

    password = request.form.get('password', '').strip()
    selected_role = request.form.get('role', 'customer')  # 'customer', 'employee', 'manager'

    # Owner login (env-based)
    if email == OWNER_USERNAME and check_password_hash(OWNER_PASSWORD, password):
        session.clear()
        session['owner_access'] = True
        session['user_name'] = email
        session['role'] = 'owner'
        session['user_role'] = 'owner'
        flash('התחברת כבעלים!', 'success')
        return redirect(url_for('index'))

    # Normal user login (SQL)
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        flash("❌ אימייל או סיסמה שגויים", "danger")
        return redirect(url_for('login'))

    # Role mismatch check
    if user.role != selected_role:
        flash('⛔ סוג המשתמש לא תואם לחשבון זה', 'danger')
        return redirect(url_for('login'))

    # -----------------------------
    # LOGIN SUCCESS — SET SESSION
    # -----------------------------
    session.clear()
    session['user_id'] = user.id
    session['user_name'] = user.email
    session['role'] = user.role
    session['user_role'] = user.role

    # MANAGER LOGIN
    if user.role == 'manager':
        employee = EmployeeData.query.filter_by(employee_id=user.id).first()
        if employee:
            session['employee_id'] = employee.employee_id
            session['employee_name'] = employee.employee_name
        flash('התחברת כמנהל!', 'success')
        return redirect(url_for('index'))

    # EMPLOYEE LOGIN
    if user.role == 'employee':
        employee = EmployeeData.query.filter_by(employee_id=user.id).first()
        if employee:
            session['employee_id'] = employee.employee_id
            session['employee_name'] = employee.employee_name
        flash('התחברת כעובד!', 'success')
        return redirect(url_for('employee_dashboard'))

    # CUSTOMER LOGIN
    if user.role == 'customer':
        flash('התחברת כלקוח!', 'success')
        return redirect(url_for('index'))

    # fallback
    flash('התחברת בהצלחה!', 'success')
    return redirect(url_for('index'))

# -----------------------------
# Logout
# -----------------------------

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    flash(" יצאת מהמערכת בהצלחה", "info")
    return redirect(url_for('login'))

# -----------------------------
# Register
# -----------------------------

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    role = request.form.get('role', 'customer')  # 'customer' or 'employee'

    if not email or not password:
        flash('אימייל וסיסמה נדרשים', 'warning')
        return redirect(url_for('login'))

    existing = User.query.filter_by(email=email).first()
    if existing:
        flash('משתמש כבר קיים עם האימייל הזה', 'warning')
        return redirect(url_for('login'))

    user = User(
        email=email,
        username=username or email,
        role=role
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    flash('נרשמת בהצלחה!', 'success')
    return redirect(url_for('login'))


# -----------------------------
# Clients (Owner only)
# -----------------------------

@app.route('/clients')
@OWNER_required
def clients():
    users = User.query.order_by(User.id.desc()).all()
    now_dt = datetime.utcnow()
    now = int(now_dt.timestamp())

    view_users = []
    for u in users:
        if u.access_expires_at:
            seconds_left = int((u.access_expires_at - now_dt).total_seconds())
        else:
            seconds_left = -1  # ללא הגבלה

        if not u.is_active:
            status_label = '⛔ חסום'
        elif u.access_expires_at and seconds_left <= 0:
            status_label = '⛔ פג תוקף'
        else:
            status_label = '✅ פעיל'

        view_users.append({
            'id': u.id,
            'username': u.username or u.email,
            'email': u.email,
            'role': u.role,
            'created_at': u.created_at,
            'last_login': u.last_login,
            'seconds_left': max(0, seconds_left),
            'status_label': status_label,
        })

    # is_owner – אם אתה משתמש בזה ב־HTML
    return render_template('clients.html', users=view_users, now=now, is_owner=True)


# -----------------------------
# Update Access (Owner only)
# -----------------------------

@app.route('/update_access', methods=['POST'])
@OWNER_required
def update_access():
    email = request.form.get('email')
    status = request.form.get('status')      # 'active' / 'blocked'
    duration = request.form.get('duration')  # שניות או '' (ללא הגבלה)

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("❌ משתמש לא נמצא", "danger")
        return redirect(url_for('clients'))

    user.is_active = (status == 'active')

    if duration and duration.isdigit():
        seconds = int(duration)
        user.access_expires_at = datetime.utcnow() + timedelta(seconds=seconds)
    else:
        user.access_expires_at = None  # ללא הגבלה

    db.session.commit()
    flash("✅ הגישה עודכנה בהצלחה", "success")
    return redirect(url_for('clients'))


# -----------------------------
# Create Reset Token (Owner only)
# -----------------------------

def create_reset_token(user):
    token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(hours=1)

    entry = PasswordResetToken(
        user_id=user.id,
        token=token,
        expires_at=expires
    )
    db.session.add(entry)
    db.session.commit()

    return token


# -----------------------------
# E-Mail Send Link (Owner only)
# -----------------------------

@app.route('/send-reset-link', methods=['POST'])
@OWNER_required
def send_reset_link():
    email = request.form.get('email')
    user = User.query.filter_by(email=email).first()

    if not user:
        flash("משתמש לא נמצא", "danger")
        return redirect(url_for('clients'))

    token = create_reset_token(user)
    reset_url = url_for('set_password', token=token, _external=True)

    msg = Message(
        "קביעת סיסמה",
        recipients=[email],
        body=f"שלום {user.username},\n\nהנה הקישור לקביעת סיסמה:\n{reset_url}\n\nבתוקף לשעה."
    )
    mail.send(msg)

    flash("קישור קביעת סיסמה נשלח!", "success")
    return redirect(url_for('clients'))


# -----------------------------
# Set Password (via token)
# -----------------------------

@app.route('/set-password', methods=['GET', 'POST'])
def set_password():

    # OWNER CAN ENTER WITHOUT TOKEN
    if session.get('owner_access'):
        return render_template('set_password.html')

    # EMPLOYEES REQUIRE TOKEN
    token = request.args.get('token')
    entry = PasswordResetToken.query.filter_by(token=token).first()

    if not entry or entry.expires_at < datetime.utcnow():
        flash("טוקן לא תקין או פג תוקף", "danger")
        return redirect(url_for('login'))

    user = User.query.get(entry.user_id)

    if request.method == 'POST':
        new_pass = request.form.get('password')
        if not new_pass:
            flash("סיסמה נדרשת", "warning")
            return redirect(request.url)

        user.password_hash = generate_password_hash(new_pass)

        db.session.delete(entry)
        db.session.commit()

        flash("הסיסמה עודכנה בהצלחה!", "success")
        return redirect(url_for('login'))

    return render_template('set_password.html')

# -----------------------------
# Delete selected users (Owner only)
# -----------------------------

@app.route('/delete_selected_users', methods=['POST'])
@OWNER_required
def delete_selected_users():
    ids = request.form.getlist('delete_ids')

    if not ids:
        flash("לא נבחרו משתמשים למחיקה", "warning")
        return redirect(url_for('clients'))

    for user_id in ids:
        user = User.query.get(user_id)
        if user:
            db.session.delete(user)

    db.session.commit()

    flash(f"נמחקו {len(ids)} משתמשים", "success")
    return redirect(url_for('clients'))


# -----------------------------
# Update role (Owner only)
# -----------------------------

@app.route('/update_role', methods=['POST'])
@OWNER_required
def update_role():
    email = request.form.get('email')
    new_role = request.form.get('role')

    if not email or not new_role:
        flash("❌ נתונים לא תקינים", "danger")
        return redirect(url_for('clients'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("❌ משתמש לא נמצא", "danger")
        return redirect(url_for('clients'))

    user.role = new_role
    db.session.commit()

    flash("✅ סוג המשתמש עודכן בהצלחה", "success")
    return redirect(url_for('clients'))

# -----------------------------
# Employee dashboard
# -----------------------------

@app.route('/employee-dashboard')
@login_required
def employee_dashboard():
    role = session.get('role')

    # OWNER 
    if session.get('owner_access'):
        return redirect(url_for('index'))

    # MANAGER 
    if role == 'manager':
        return redirect(url_for('index'))

    # EMPLOYEE 
    if role == 'employee':
        return redirect(url_for('clock_in_out'))

    return redirect(url_for('index'))




# ----------------------
# Getting Format All Percentage Currency : Form 
# ----------------------

# Safely convert a value to a float פונקציה להמיר ערכים למספרים
def to_float(value):
    try:
        cleaned = str(value).replace(',', '').strip()
        if cleaned.lower() in ('', 'n/a', 'none'):
            return 0.0
        return float(cleaned)
    except (ValueError, TypeError):
        return 0.0

def format_currency(value):
    """Formats numbers as currency (Shekel symbol added)."""
    if not value or value == 0.0:
        return '0.00'
    return f"{value:,.2f}"

def sanitize_input(value, is_percentage=False, allow_nan=True):
    try:
        # Handle None or empty values gracefully
        if not value:
            return 0.0 if allow_nan else "N/A"

        # Remove unwanted characters like ',' and '%', and trim spaces
        if isinstance(value, str):
            value = value.replace(",", "").replace("%", "").strip()

        # Convert the sanitized string to a float
        numeric_value = float(value)

        # Handle percentage-specific logic
        if is_percentage:
            # Convert decimal to percentage if it's between 0 and 1
            if 0 <= numeric_value <= 1:
                return numeric_value * 100
            return numeric_value  # Already a percentage

        return numeric_value  # Return sanitized float for non-percentage values

    except (ValueError, TypeError):
        # Gracefully handle invalid inputs
        return 0.0 if allow_nan else "N/A"

# ----------------------
# Getting Clean Number Value Format Helper  
# ----------------------

def clean_number(value):
    try:
        return float(str(value).replace("₪", "").replace(",", "").strip())
    except:
        return 0.0

# ----------------------
# Getting Format Date Helper : Form 
# ----------------------

def format_date_for_display(date_str):
    """Convert YYYY-MM-DD to DD/MM/YYYY for display"""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').strftime('%d/%m/%Y')
    except Exception:
        return date_str  # fallback if already formatted or invalid

def format_date_for_input(date_str):
    """Convert DD/MM/YYYY to YYYY-MM-DD for HTML input"""
    try:
        return datetime.strptime(date_str, '%d/%m/%Y').strftime('%Y-%m-%d')
    except Exception:
        return date_str

# ----------------------
# Getting Days in a Month Holidays Weekend: Form 
# ----------------------

#  Generate full day list with Hebrew weekday names
def get_days_in_month(year, month):
    num_days = calendar.monthrange(int(year), int(month))[1]
    hebrew_days = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי', 'שבת']
    days_data = []

    for day in range(1, num_days + 1):
        date = datetime(int(year), int(month), day)
        hebrew_day = hebrew_days[date.weekday()]
        formatted_date = date.strftime('%d-%m-%Y')

        days_data.append({
            "day": hebrew_day,
            "date": formatted_date
        })

    return days_data

@app.template_filter('format_date')
@login_required
def format_date(value, fmt='%d/%m/%Y'):
    try:
        return value.strftime(fmt)
    except Exception:
        try:
            return datetime.strptime(value, '%Y-%m-%d').strftime(fmt)
        except Exception:
            return value  # fallback if everything fails

@app.route('/update_month_year', methods=['POST'])
@login_required
def update_month_year():
    data = request.get_json()
    year = data.get("employeeYear")
    month = data.get("employeeMonth")

    session['employeeMonth'] = month
    session['employeeYear'] = year

    days_data = get_days_in_month(year, month)
    return jsonify(success=True, days_data=days_data)

# -----------------------------
# Company Name Add To Timesheet From Json
# -----------------------------

def load_company_data():
    json_path = os.path.join(os.path.dirname(__file__), "company.json")
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

company_data = load_company_data()

# ----------------------
# Helper Calculate
# ----------------------
def calculate_hours(start_time_str, end_time_str):
    """
    Calculate total hours between start and end times.
    Handles overnight shifts (e.g., 22:00 → 02:00).
    Returns float hours.
    """
    fmt = "%H:%M"
    try:
        start = datetime.strptime(start_time_str, fmt)
        end = datetime.strptime(end_time_str, fmt)

        # If end time is earlier than start → assume next day
        if end < start:
            end += timedelta(days=1)

        diff = end - start
        return round(diff.total_seconds() / 3600, 2)

    except Exception:
        return 0.0


# ----------------------
# HoursCard clock_hours_data.json
# ----------------------

# Greate Main Folder clock_hours_data.json

BASE_DIR = os.path.join(app.root_path, "clock_hours_data")

def get_clock_file(employee_name, year, month):
    safe_name = employee_name.replace(" ", "_")
    year_folder = os.path.join(BASE_DIR, str(year))
    month_folder = os.path.join(year_folder, f"month_{str(month).zfill(2)}")
    os.makedirs(month_folder, exist_ok=True)
    filename = f"clock_hours_{safe_name}_{year}-{str(month).zfill(2)}.json"
    return os.path.join(month_folder, filename)


def load_clock_hours(employee_name, year, month):
    file_path = get_clock_file(employee_name, year, month)

    if not os.path.exists(file_path):
        return {
            "employee_id": "",
            "employee_name": employee_name,
            "id_number": "",
            "hours_table_clock": {"work_day_entries": []}
        }

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

            data.setdefault("employee_id", "")
            data.setdefault("employee_name", employee_name)
            data.setdefault("id_number", "")
            data.setdefault("hours_table_clock", {"work_day_entries": []})

            return data

    except:
        return {
            "employee_id": "",
            "employee_name": employee_name,
            "id_number": "",
            "hours_table_clock": {"work_day_entries": []}
        }


def save_clock_hours_file(employee_name, year, month, data):
    file_path = get_clock_file(employee_name, year, month)

    data.setdefault("employee_id", "")
    data.setdefault("employee_name", employee_name)
    data.setdefault("id_number", "")
    data.setdefault("hours_table_clock", {"work_day_entries": []})

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)



def normalize_keys(data_dict):
    return {k.replace("_", "-"): v for k, v in data_dict.items()} if isinstance(data_dict, dict) else data_dict

def denormalize_keys(data_dict):
    return {k.replace("-", "_"): v for k, v in data_dict.items()} if isinstance(data_dict, dict) else data_dict

# ----------------------
#  Timesheet Page Entry 
# ----------------------

@app.route("/timesheet", methods=["GET", "POST"])
@login_required
def timesheet():
    today = datetime.today()

    months = [
        'ינואר', 'פברואר', 'מרץ', 'אפריל', 'מאי', 'יוני',
        'יולי', 'אוגוסט', 'ספטמבר', 'אוקטובר', 'נובמבר', 'דצמבר'
    ]
    years = list(range(2020, 2041))

    role = session.get("role")

    # === DETERMINE EMPLOYEE ===
    if role == "owner":
        # בעל עסק יכול לבחור עובד
        employee_id = (
            request.args.get("employee_id")
            or request.form.get("employee_id")
            or session.get("employee_id")
        )
    else:
        # עובד רגיל → תמיד הוא עצמו
        employee_id = session.get("employee_id")

    # אם עדיין אין עובד → לא מוחקים session → רק מחזירים למסך בחירה
    if not employee_id:
        flash("יש לבחור עובד.", "danger")
        return redirect(url_for("clock_in_out"))

    # טוענים את העובד
    employee = EmployeeData.query.get(employee_id)
    if not employee:
        flash("שגיאה: העובד לא נמצא.", "danger")
        return redirect(url_for("clock_in_out"))

    # שומרים את העובד ב-session (לא מוחקים)
    session["employee_id"] = employee_id

    # === DETERMINE MONTH/YEAR ===
    selected_month = (
        request.args.get("month")
        or request.form.get("timesheetMonth")
        or session.get("timesheet_month")
        or f"{today.month:02d}"
    )

    selected_year = (
        request.args.get("year")
        or request.form.get("timesheetYear")
        or session.get("timesheet_year")
        or str(today.year)
    )

    selected_month = str(selected_month).zfill(2)
    selected_year = str(selected_year)

    # שומרים בחירה (לא מוחקים)
    session["timesheet_month"] = selected_month
    session["timesheet_year"] = selected_year

    # === LOAD JSON FILE ===
    employee_name = employee.employee_name.replace(" ", "_")
    month_data = load_clock_hours(employee_name, selected_year, selected_month)

    # מבטיחים שהקובץ מכיל נתוני עובד
    month_data["employee_id"] = employee_id
    month_data["employee_name"] = employee.employee_name
    month_data["id_number"] = employee.id_number

    hours_table_clock = month_data.get("hours_table_clock", {"work_day_entries": []})
    timesheet_data = hours_table_clock.get("work_day_entries", [])

    # === CALCULATE HOURS ===
    for row in timesheet_data:
        st = row.get("start_time")
        et = row.get("end_time")

        if st and et:
            st_dt = datetime.strptime(st, "%H:%M")
            et_dt = datetime.strptime(et, "%H:%M")
            if et_dt < st_dt:
                et_dt += timedelta(days=1)
            diff = et_dt - st_dt
            row["totalHours"] = round(diff.total_seconds() / 3600, 2)
        else:
            row["totalHours"] = ""

    return render_template(
        "timesheet.html",
        months=months,
        years=years,
        selected_month=selected_month,
        selected_year=selected_year,
        employee_id=employee_id,
        employee_name=employee.employee_name,
        id_number=employee.id_number,
        timesheet_data=timesheet_data
    )


# ----------------------
# HoursCard Api Get timesheet
# ----------------------

@app.route('/api/savetimesheet', methods=['POST'])
@login_required
def api_save_timesheet():
    data = request.get_json()

    employee_id = str(data.get("employee_id"))
    employee = EmployeeData.query.get(employee_id)
    employee_name = employee.employee_name.replace(" ", "_")
    id_number = employee.id_number

    date_str = data.get("date")
    start_iso = data.get("startTime")
    end_iso = data.get("endTime")
    task = data.get("task", "")

    start_hm = start_iso[11:16]
    end_hm = end_iso[11:16]

    st = datetime.strptime(start_hm, "%H:%M")
    et = datetime.strptime(end_hm, "%H:%M")
    if et < st:
        et += timedelta(days=1)
    total_hours = round((et - st).total_seconds() / 3600, 2)

    year, month, _ = date_str.split("-")

    db = load_clock_hours(employee_name, year, month)

    db["employee_id"] = employee_id
    db["employee_name"] = employee.employee_name
    db["id_number"] = id_number

    entries = db["hours_table_clock"]["work_day_entries"]

    entry = next((e for e in entries if e["date"] == date_str), None)

    if not entry:
        entry = {
            "date": date_str,
            "day": "",
            "saturday": "",
            "holiday": "",
            "start_time": "",
            "end_time": "",
            "task": "",
            "totalHours": ""
        }
        entries.append(entry)

    entry["start_time"] = start_hm
    entry["end_time"] = end_hm
    entry["task"] = task
    entry["totalHours"] = str(total_hours)

    save_clock_hours_file(employee_name, year, month, db)

    return jsonify({"success": True, "entry": entry})


# ----------------------
# HoursCard Clock In: timesheet
# ----------------------

@app.route('/api/clockin', methods=['POST'])
@login_required
def api_clockin():
    emp_id = session.get("employee_id")

    if not emp_id:
        return {"status": "error", "message": "No employee selected"}, 400

    emp_id = str(emp_id)

    # Load employee info
    employee = EmployeeData.query.get(emp_id)
    if not employee:
        return {"status": "error", "message": "Employee not found"}, 400

    employee_name = employee.employee_name.replace(" ", "_")
    id_number = employee.id_number

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")

    year, month, _ = date_str.split('-')

    #  Load the correct file for this employee + month
    db = load_clock_hours(employee_name, year, month)

    #  Ensure employee info exists in JSON
    db["employee_id"] = emp_id
    db["employee_name"] = employee.employee_name
    db["id_number"] = id_number

    hours_table = db.setdefault("hours_table_clock", {
        "work_day_entries": []
    })

    # Find existing entry for today
    day = next(
        (d for d in hours_table["work_day_entries"] if d.get("date") == date_str),
        None
    )

    # If no entry exists → create one
    if not day:
        weekday = now.weekday()  # 0=Mon, 6=Sun
        hebrew_days = ["שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת", "ראשון"]

        day = {
            "date": date_str,
            "day": hebrew_days[weekday],
            "saturday": "שבת" if weekday == 5 else "",
            "holiday": "",
            "start_time": "",
            "end_time": "",
            "task": "",
            "totalHours": ""
        }

        hours_table["work_day_entries"].append(day)

    # Update start time ONLY
    day["start_time"] = time_str

    #  Save file for this employee + month
    save_clock_hours_file(employee_name, year, month, db)

    return {"status": "ok", "start": time_str}

# ----------------------
# HoursCard API: Clock Out
# ----------------------

@app.route('/api/clockout', methods=['POST'])
@login_required
def api_clockout():
    emp_id = session.get("employee_id")

    if not emp_id:
        return {"status": "error", "message": "No employee selected"}, 400

    emp_id = str(emp_id)

    # Load employee info
    employee = EmployeeData.query.get(emp_id)
    if not employee:
        return {"status": "error", "message": "Employee not found"}, 400

    employee_name = employee.employee_name.replace(" ", "_")
    id_number = employee.id_number

    data = request.get_json()
    task = (data.get("task") or "").strip()
    end_iso = data.get("endTime")

    if not end_iso:
        return {"status": "error", "message": "Missing end time"}, 400

    # Convert ISO → datetime
    end_dt = datetime.fromisoformat(end_iso.replace("Z", ""))

    date_str = end_dt.strftime("%Y-%m-%d")
    time_str = end_dt.strftime("%H:%M")

    year, month, _ = date_str.split('-')

    #  Load file for this employee + month
    db = load_clock_hours(employee_name, year, month)

    #  Ensure employee info exists in JSON
    db["employee_id"] = emp_id
    db["employee_name"] = employee.employee_name
    db["id_number"] = id_number

    hours_table = db.setdefault("hours_table_clock", {
        "work_day_entries": []
    })

    # Find today's entry
    day = next(
        (d for d in hours_table["work_day_entries"] if d.get("date") == date_str),
        None
    )

    # If no entry exists → create one
    if not day:
        weekday = end_dt.weekday()
        hebrew_days = ["שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת", "ראשון"]

        day = {
            "date": date_str,
            "day": hebrew_days[weekday],
            "saturday": "שבת" if weekday == 5 else "",
            "holiday": "",
            "start_time": "",
            "end_time": "",
            "task": "",
            "totalHours": ""
        }
        hours_table["work_day_entries"].append(day)

    # Update end time + task
    day["end_time"] = time_str
    day["task"] = task

    # Calculate total hours only if start exists
    if day["start_time"]:
        start_dt = datetime.strptime(f"{date_str} {day['start_time']}", "%Y-%m-%d %H:%M")
        end_dt2 = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")

        # Night shift fix
        if end_dt2 < start_dt:
            end_dt2 += timedelta(days=1)

        diff_hours = round((end_dt2 - start_dt).total_seconds() / 3600, 2)
        day["totalHours"] = str(diff_hours)

    #  Save file for this employee + month
    save_clock_hours_file(employee_name, year, month, db)

    return {"status": "ok", "end": time_str, "task": task}


# ----------------------
# CLOCK IN OUT PAGE
# ----------------------

@app.route("/clock-in-out", methods=["GET"])
@employee_or_manager_required
def clock_in_out():
    role = session.get("role")
    today = datetime.today()

    months = [
        'ינואר', 'פברואר', 'מרץ', 'אפריל', 'מאי', 'יוני',
        'יולי', 'אוגוסט', 'ספטמבר', 'אוקטובר', 'נובמבר', 'דצמבר'
    ]
    years = list(range(2020, 2041))
    employees = EmployeeData.query.all()

    # === ALWAYS take GET first ===
    employee_id = request.args.get("employee_id")
    selected_month = request.args.get("month")
    selected_year = request.args.get("year")

    # === EMPLOYEE → ALWAYS TODAY ===
    if role == "employee":
        employee_id = session.get("employee_id")
        selected_month = f"{today.month:02d}"
        selected_year = str(today.year)

    # === MANAGER → GET → SESSION → TODAY ===
    else:
        if not employee_id:
            employee_id = session.get("employee_id", "")
        if not selected_month:
            selected_month = session.get("selected_month", f"{today.month:02d}")
        if not selected_year:
            selected_year = session.get("selected_year", str(today.year))

        # Save manager selection
        session["employee_id"] = employee_id
        session["selected_month"] = selected_month
        session["selected_year"] = selected_year

    # === Load employee info ===
    emp = EmployeeData.query.get(employee_id)
    if not emp:
        return redirect(url_for("clock_in_out"))

    employee_name = emp.employee_name.replace(" ", "_")

    # === LOAD NEW CLOCK FILE ===
    month_data = load_clock_hours(employee_name, selected_year, selected_month)

    #  Inject employee info if missing
    month_data["employee_id"] = employee_id
    month_data["employee_name"] = emp.employee_name
    month_data["id_number"] = emp.id_number

    hours_table_clock = month_data.get(
        "hours_table_clock",
        {"work_day_entries": []}
    )

    # === Render ===
    return render_template(
        "clock_in_out.html",
        employees=employees,
        selected_employee_id=str(employee_id),
        employeeMonth=selected_month,
        employeeYear=selected_year,
        months=months,
        years=years,
        time=time,
        hours_table_clock=hours_table_clock,
        form_data={
            "employee_id": employee_id,
            "employee_name": emp.employee_name,
            "id_number": emp.id_number
        },
        role=role
    )

# ----------------------
# Save Employee Clock Hours
# ----------------------

@app.route("/save_clock_hours", methods=["POST"])
@login_required
def save_clock_hours():
    data = request.get_json() or {}

    # 1. Extract identifiers
    emp_id = str(data.get("employee_id", "")).strip()
    month = str(data.get("month", "")).zfill(2)
    year = str(data.get("year", "")).strip()

    if not emp_id or not month or not year:
        return jsonify({"status": "error", "message": "Missing employee/month/year"}), 400

    # Load employee info
    employee = EmployeeData.query.get(emp_id)
    if not employee:
        return jsonify({"status": "error", "message": "Employee not found"}), 400

    employee_name = employee.employee_name.replace(" ", "_")
    id_number = employee.id_number

    # 2. Load existing JSON for this employee + month
    db = load_clock_hours(employee_name, year, month)

    # ⭐ Ensure employee info is stored in JSON
    db["employee_id"] = emp_id
    db["employee_name"] = employee.employee_name
    db["id_number"] = id_number

    hours_table = db.setdefault("hours_table_clock", {
        "work_day_entries": []
    })

    # 3. Incoming entries
    new_entries = data.get("hours_table_clock", {}).get("work_day_entries", [])
    if not isinstance(new_entries, list):
        new_entries = []

    # 4. Build map of existing entries
    existing_map = {}
    for d in hours_table.get("work_day_entries", []):
        date = d.get("date")
        if date:
            existing_map[date] = d

    # 5. Merge new entries
    for entry in new_entries:
        date = entry.get("date")
        if not date:
            continue

        merged = {
            "date": date,
            "day": entry.get("day", ""),
            "saturday": entry.get("saturday", ""),
            "holiday": entry.get("holiday", ""),
            "start_time": entry.get("start_time", ""),
            "end_time": entry.get("end_time", ""),
            "task": entry.get("task", ""),
            "totalHours": entry.get("totalHours", "")
        }

        existing_map[date] = merged

    # 6. Save merged list back (sorted by date)
    def sort_key(item):
        try:
            return datetime.strptime(item["date"], "%Y-%m-%d")
        except:
            return datetime.min

    hours_table["work_day_entries"] = sorted(existing_map.values(), key=sort_key)

    # 7. Save JSON file for this employee + month
    save_clock_hours_file(employee_name, year, month, db)

    return jsonify({"status": "ok", "message": "Clock hours saved"}), 200

# ----------------------
# Api Record Time
# ----------------------

@app.route('/api/record_time', methods=['POST'])
@login_required
def api_record_time():
    data = request.get_json() or {}

    employee_id = str(data.get("employee_id", "")).strip()
    action_type = data.get("type")  # START or END
    task = data.get("task", "").strip()

    if not employee_id or not action_type:
        return jsonify({"success": False, "message": "Missing data"}), 400

    if action_type not in ("START", "END"):
        return jsonify({"success": False, "message": "Invalid type"}), 400

    # Load employee info
    emp = EmployeeData.query.get(employee_id)
    if not emp:
        return jsonify({"success": False, "message": "Employee not found"}), 400

    employee_name = emp.employee_name.replace(" ", "_")
    id_number = emp.id_number

    now = datetime.now()
    iso_now = now.isoformat(timespec='minutes')

    # Extract date + HH:MM
    date_str = now.strftime("%Y-%m-%d")
    hm = now.strftime("%H:%M")

    year = now.strftime("%Y")
    month = now.strftime("%m")

    # Load JSON file for this employee + month
    db = load_clock_hours(employee_name, year, month)

    # Ensure employee info exists in JSON
    db["employee_id"] = employee_id
    db["employee_name"] = emp.employee_name
    db["id_number"] = id_number

    entries = db["hours_table_clock"]["work_day_entries"]

    # Find or create entry for today
    entry = next((e for e in entries if e["date"] == date_str), None)
    if not entry:
        entry = {
            "date": date_str,
            "day": now.strftime("%A"),
            "saturday": "",
            "holiday": "",
            "start_time": "",
            "end_time": "",
            "task": "",
            "totalHours": ""
        }
        entries.append(entry)

    # START → save start_time + task
    if action_type == "START":
        entry["start_time"] = hm
        entry["task"] = task
        session["clock_start"] = iso_now
        session["clock_task"] = task

    # END → save end_time + totalHours
    elif action_type == "END":
        entry["end_time"] = hm
        session["clock_end"] = iso_now

        # Calculate total hours if start exists
        if entry["start_time"]:
            st = datetime.strptime(entry["start_time"], "%H:%M")
            et = datetime.strptime(hm, "%H:%M")
            if et < st:
                et += timedelta(days=1)
            total_hours = round((et - st).total_seconds() / 3600, 2)
            entry["totalHours"] = str(total_hours)

    # Save JSON file
    save_clock_hours_file(employee_name, year, month, db)

    return jsonify({
        "success": True,
        "timestamp": iso_now,
        "type": action_type,
        "entry": entry
    })

# ----------------------
# OWNER Button Delete Day Clock Hours
# ----------------------

@app.route('/api/clear_day', methods=['POST'])
@login_required
def clear_day():
    # Only OWNER can clear days
    if not session.get("owner_access"):
        return jsonify({"message": "רק בעלים יכול לאפס יום"}), 403

    data = request.get_json()
    date = data.get("date")

    # Employee ID must come from session (owner selected employee)
    employee_id = str(session.get("employee_id") or "").strip()
    if not employee_id:
        return jsonify({"message": "לא נבחר עובד"}), 400

    # Month/year from session
    selected_month = session.get("selected_month")
    selected_year = session.get("selected_year")

    if not selected_month or not selected_year:
        return jsonify({"message": "חודש או שנה חסרים"}), 400

    # Load employee info
    emp = EmployeeData.query.get(employee_id)
    if not emp:
        return jsonify({"message": "העובד לא נמצא"}), 400

    employee_name = emp.employee_name.replace(" ", "_")

    #  Load the correct file for this employee + month
    db = load_clock_hours(employee_name, selected_year, selected_month)

    hours_table = db.setdefault("hours_table_clock", {
        "work_day_entries": []
    })

    entries = hours_table["work_day_entries"]

    # Clear the selected day
    cleared = False
    for entry in entries:
        if entry.get("date") == date:
            entry["start_time"] = ""
            entry["end_time"] = ""
            entry["task"] = ""
            entry["totalHours"] = ""
            cleared = True
            break

    # Save file back
    save_clock_hours_file(employee_name, selected_year, selected_month, db)

    if cleared:
        return jsonify({"message": "היום אופס בהצלחה"})
    else:
        return jsonify({"message": "לא נמצא יום זה"}), 200

# --------------------
# Clear Employee Form Data
# ----------------------

@app.route('/clear_clock_display', methods=['POST'])
@login_required
def clear_clock_data():
    # Only OWNER can clear all clock data
    if not session.get("owner_access"):
        flash("⛔ רק בעלים יכול לנקות את כל נתוני השעות.", "danger")
        return redirect(url_for('clock_in_out'))

    emp_id = str(session.get('employee_id') or '').strip()

    if not emp_id:
        flash("לא ניתן לנקות — לא נבחר עובד.", "danger")
        return redirect(url_for('clock_in_out'))

    session.pop('hours_table_clock', None)

    flash("נתוני הדוח נוקו מהתצוגה בלבד (ללא מחיקת קבצים).", "info")
    return redirect(url_for('clock_in_out'))

# --------------------
# Delete Employee Select Form Folder
# ----------------------
@app.route('/delete_clock_file', methods=['POST'])
@login_required
def delete_clock_file():
    if not session.get("owner_access"):
        flash("⛔ רק בעלים יכול למחוק קובץ שעות.", "danger")
        return redirect(url_for('clock_in_out'))

    emp_id = str(session.get('employee_id') or '').strip()
    year = str(session.get('selected_year') or '').strip()
    month = str(session.get('selected_month') or '').zfill(2)

    if not emp_id or not year or not month:
        flash("לא ניתן למחוק — חסר עובד/שנה/חודש.", "danger")
        return redirect(url_for('clock_in_out'))

    emp = EmployeeData.query.get(emp_id)
    employee_name = emp.employee_name.replace(" ", "_")

    #  הנתיב הנכון לפי המבנה שלך
    folder_path = os.path.join("clock_hours_data", year, f"month_{month}")
    filename = f"clock_hours_{employee_name}_{year}-{month}.json"
    file_path = os.path.join(folder_path, filename)

    if os.path.exists(file_path):
        os.remove(file_path)
        flash(f"קובץ {filename} נמחק בהצלחה.", "info")
    else:
        flash("לא נמצא קובץ למחיקה.", "warning")

    # מנקה תצוגה בלבד
    session['hours_table_clock'] = {"work_day_entries": []}

    return redirect(url_for('clock_in_out'))

# ----------------------
# Get Employee Monthly Hours From Hourscard To Index Page
# ----------------------

@app.route("/get_clock_hours", methods=["GET"])
@login_required
def get_clock_hours():
    employee_id = request.args.get("employee_id")
    month = request.args.get("month")
    year = request.args.get("year")

    if not employee_id or not month or not year:
        return jsonify({})

    month = str(month).zfill(2)

    emp = EmployeeData.query.get(employee_id)
    if not emp:
        return jsonify({})

    employee_name = emp.employee_name.replace(" ", "_")

    data = load_clock_hours(employee_name, year, month)

    # Inject missing info
    data["employee_id"] = employee_id
    data["employee_name"] = emp.employee_name
    data["id_number"] = emp.id_number

    entries = data["hours_table_clock"]["work_day_entries"]

    def convert_date(d):
        try:
            return datetime.strptime(d, "%Y-%m-%d").strftime("%d/%m/%Y")
        except:
            return d

    formatted = []
    for e in entries:
        formatted.append({
            "date": convert_date(e.get("date", "")),
            "day": e.get("day", ""),
            "start_time": e.get("start_time", ""),
            "end_time": e.get("end_time", ""),
            "task": e.get("task", ""),
            "totalHours": e.get("totalHours", "")
        })

    return jsonify({
        "employee_id": employee_id,
        "employee_name": emp.employee_name,
        "id_number": emp.id_number,
        "year": year,
        "month": month,
        "entries": formatted
    })


# ----------------------
# Employee Bank Account Page
# ----------------------

@app.route('/employee/<int:employee_id>/bank', methods=['GET', 'POST'])
@login_required
def manage_bank_account(employee_id):
    employee = EmployeeData.query.get_or_404(employee_id)
    bank_account = BankAccount.query.filter_by(employee_id=employee_id).first()

    if request.method == 'POST':
        # Get form data
        bank_code = request.form.get('bank_code')
        branch_code = request.form.get('branch_code')
        account_number = request.form.get('account_number')

        # Add validation to prevent IntegrityError on empty submission
        if not bank_code or not branch_code or not account_number:
            flash('כל שדות פרטי הבנק הינם חובה', 'error')
            return redirect(url_for('manage_bank_account', employee_id=employee_id))

        if not bank_account:
            bank_account = BankAccount(employee_id=employee_id)
            db.session.add(bank_account)
        
        bank_account.bank_code = bank_code
        bank_account.branch_code = branch_code
        bank_account.account_number = account_number
        
        db.session.commit()
        flash('פרטי הבנק עודכנו בהצלחה', 'success')
        return redirect(url_for('manage_bank_account', employee_id=employee_id))

    return render_template('manage_bank.html', employee=employee, bank_account=bank_account)


# Route to delete an employee's bank account
@app.route('/employee/<int:employee_id>/bank/delete', methods=['POST'])
@login_required
def delete_bank_account(employee_id):
    bank_account = BankAccount.query.filter_by(employee_id=employee_id).first_or_404()
    db.session.delete(bank_account)
    db.session.commit()
    flash('פרטי הבנק נמחקו בהצלחה', 'success')
    return redirect(url_for('manage_bank_account', employee_id=employee_id))
       
# ----------------------
# Hours File Load Handling
# ----------------------

def get_base_dir():
    base_dir = os.path.join(app.root_path, "hours_data")
    os.makedirs(base_dir, exist_ok=True)
    return base_dir

def load_hours(year):
    base_dir = get_base_dir()
    year_folder = os.path.join(base_dir, f"hours_data_{year}")
    json_path = os.path.join(year_folder, f"hours_data_{year}.json")

    if not os.path.exists(json_path):
        return {}

    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_hours(data, year):
    base_dir = get_base_dir()
    year_folder = os.path.join(base_dir, f"hours_data_{year}")
    os.makedirs(year_folder, exist_ok=True)

    json_path = os.path.join(year_folder, f"hours_data_{year}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ----------------------
# Check If Employee ID Months Years Exists On Data   
# ----------------------

def entry_exists_in_csv(employee_id, month_key):
    try:
        with open('hours_data.csv', 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['employee_id'] == employee_id and row['month'] == month_key:
                    return row
    except FileNotFoundError:
        pass

    return {
        'employee_id': '',
        'employee_name': '',
        'month': '',
        'section': '',
        'total_salary_pension_funds': '',
        'amount_tax_credit_points_monthly': '',
        'income_tax_before_credit': '',
        'final_city_tax_benefit': '',
        'monthly_city_tax_tops': '',
        'date_of_birth': '',
        'basic_salary': '',
        'city_value_percentage': '',
        'additional_payments': '',
        'above_ceiling_value': '',
        'above_ceiling_fund': '',
        'above_ceiling_compensation': '',
        'tax_level_precente': '',
        'tax_credit_points': '',
        'net_value': '',
        'gross_salary': '',
        'gross_taxable': '',
        'pension_fund': '',
        'compensation': '',
        'study_fund': '',
        'disability': '',
        'miscellaneous': '',
        'national_insurance': '',
        'salary_tax': '',
        'total_employer_contributions': '',
        'employee_pension_fund': '',
        'self_employed_pension_fund': '',
        'study_fund_deductions': '',
        'miscellaneous_deductions': '',
        'national_insurance_deductions': '',
        'health_insurance_deductions': '',
        'income_tax': '',
        'advance_payment_salary': '',
        'total_deductions': '',
        'total_salary_cost': '',
        'total_missing_hours': '',
        'total_work_days': '',
        'totals_lunch_value': '',
        'net_payment': '',
        'cars_value': '',
        'final_extra_hours_weekend': '',
        'final_extra_hours_regular': '',
        'food_break_unpaid_salary': '',
        'hours125_regular_salary': '',
        'hours150_regular_salary': '',
        'hours150_holidays_saturday_salary': '',
        'hours175_holidays_saturday_salary': '',
        'hours200_holidays_saturday_salary': '',
        'sick_days_salary': '',
        'sick_days_entitlement': '',
        'vacation_days_salary': '',
        'vacation_days_entitlement': ''
    }

# ----------------------
# Protect Main Page , Index: Form Page
# ----------------------

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    # Redirect employees to their own dashboard
    if session.get('role') == 'employee':
        return redirect(url_for('employee_dashboard'))

    # ----- Setup -----
    months = ['ינואר', 'פברואר', 'מרץ', 'אפריל', 'מאי', 'יוני',
              'יולי', 'אוגוסט', 'ספטמבר', 'אוקטובר', 'נובמבר', 'דצמבר']
    years = list(range(2020, 2041))
    employees = EmployeeData.query.order_by(EmployeeData.employee_name).all()

    today = datetime.today()
    default_month = f"{today.month:02d}"
    default_year = str(today.year)

    # OWNER session keys
    session.setdefault('employee_id', None)
    session.setdefault('selected_month', default_month)
    session.setdefault('selected_year', default_year)
    session.setdefault('employee_data', {})
    session.setdefault('table_data', {})
    session.setdefault('hours_table', {})

    # ----- Handle POST -----
    if request.method == 'POST':
        form_type = request.form.get('form_type')

        if form_type == 'save_all_data':
            try:
                selected_year = request.form.get('employeeYear', '').strip() or session['selected_year']
                selected_month = request.form.get('employeeMonth', '').strip() or session['selected_month']
                selected_employee_id = request.form.get('employee_id', '').strip() or session['employee_id']

                if not selected_employee_id:
                    flash("נא לבחור עובד לפני שמירה.", "warning")
                    return redirect(url_for('index'))

                # Save to OWNER session
                session['employee_id'] = selected_employee_id
                session['selected_month'] = selected_month
                session['selected_year'] = selected_year

                selected_month_str = str(selected_month).zfill(2)
                selected_year_str = str(selected_year)

                date_key = f"{selected_month}/{selected_year}"
                month_key = f"{selected_year_str}-{selected_month_str}"

                if not selected_month or not selected_year:
                    flash("נא למלא חודש ושנה!", "warning")
                    return redirect(url_for('index'))

                             # טוענים עובד רק אם יש ID
                employee = EmployeeData.query.get(selected_employee_id)
                if not employee:
                    flash("העובד לא נמצא", "danger")
                    return redirect(url_for('index'))

                employee_name = employee.employee_name

                # Prevent duplicates
                existing = EmployeeData.query.filter_by(employee_id=selected_employee_id, date=date_key).first()
                if existing or entry_exists_in_csv(selected_employee_id, month_key):
                    flash("הנתונים כבר קיימים — טוען נתונים", "info")
                    return redirect(url_for(
                        'index',
                        employee_id=selected_employee_id,
                        month=selected_month,
                        year=selected_year
                    ))

                # Parse hours table JSON
                hours_table_json = request.form.get('hours_table_data')
                table_data = {
                    'work_day_entries': [],
                    'monthly_totals': {},
                    'paid_totals': {},
                    'tax': {}
                }

                if hours_table_json:
                    try:
                        parsed = json.loads(hours_table_json)
                        if isinstance(parsed, dict) and 'hours_table' in parsed:
                            parsed = parsed['hours_table']
                        table_data['work_day_entries'] = parsed.get('work_day_entries', [])
                        table_data['monthly_totals'] = parsed.get('monthly_totals', {})
                        table_data['paid_totals'] = parsed.get('paid_totals', {})
                        table_data['tax'] = parsed.get('tax', {})
                        session['table_data'] = parsed
                    except json.JSONDecodeError:
                        flash("שגיאה בקריאת נתוני שעות העבודה", "danger")
                        session['table_data'] = {}

                # Compute yearly totals
                try:
                    all_hours_snapshot = load_hours(selected_year) or {}
                    yearly_totals = compute_yearly_totals(
                        all_hours=all_hours_snapshot,
                        employee_id=selected_employee_id,
                        year=selected_year,
                        current_month=selected_month,
                        current_tax=table_data.get('tax', {})
                    ) or {}
                except Exception:
                    yearly_totals = {}

                table_data.setdefault('tax', {})
                table_data['tax'].update(yearly_totals)

                # Save to hours.json
                all_hours = load_hours(selected_year) or {}
                all_hours.setdefault(str(selected_employee_id), {})
                all_hours[str(selected_employee_id)]["employee_name"] = employee_name
                all_hours[str(selected_employee_id)][month_key] = {"hours_table": table_data}
                save_hours(all_hours, selected_year)

                # Build form_data
                form_data = request.form.to_dict(flat=True)
                form_data['employee_id'] = selected_employee_id
                form_data['employee_name'] = employee_name
                form_data['employeeMonth'] = selected_month
                form_data['employeeYear'] = selected_year
                form_data['date'] = date_key
                form_data.update(yearly_totals)
                form_data.update(table_data.get('monthly_totals', {}))
                form_data.update(table_data.get('paid_totals', {}))
                form_data.update(table_data.get('tax', {}))

                session['employee_data'] = form_data
                session['month_result'] = date_key
                session['hours_table'] = table_data

                # Save to DB
                new_tax_entry = EmployeeData(**form_data)
                db.session.add(new_tax_entry)
                db.session.commit()

                # Save to CSV
                row = {
                    'employee_id': selected_employee_id,
                    'employee_name': employee_name,
                    'month': month_key
                }
                row.update(table_data.get('tax', {}))
                row.update(table_data.get('monthly_totals', {}))
                row.update(table_data.get('paid_totals', {}))

                flash("הנתונים נשמרו בהצלחה!", "success")
                return redirect(url_for(
                    'index',
                    employee_id=selected_employee_id,
                    month=selected_month,
                    year=selected_year
                ))

            except Exception as e:
                db.session.rollback()
                flash(f"שגיאה בעת השמירה: {str(e)}", "danger")
                return redirect(url_for('index'))

    # ----- Handle GET -----
    selected_employee_id = request.args.get('employee_id') or session.get('employee_id', '')
    selected_month = request.args.get('month') or session.get('selected_month', default_month)
    selected_year = request.args.get('year') or session.get('selected_year', default_year)

    # Save selection
    session['employee_id'] = selected_employee_id
    session['selected_month'] = selected_month
    session['selected_year'] = selected_year

    # Build month_key
    selected_month_str = str(selected_month).zfill(2)
    selected_year_str = str(selected_year)
    month_key = f"{selected_year_str}-{selected_month_str}"

    # Load hours JSON
    all_hours = load_hours(selected_year) or {}
    employee_json = all_hours.get(str(selected_employee_id), {}) if selected_employee_id else {}
    month_json = employee_json.get(month_key, {})

    hours_table = month_json.get("hours_table", {})
    default_hours = {
        'work_day_entries': [],
        'monthly_totals': {},
        'paid_totals': {},
        'tax': {}
    }
    for k, v in default_hours.items():
        hours_table.setdefault(k, v)

    # Build form_data
    form_data = {}
    form_data.update(session.get('employee_data', {}))

    # Merge CSV snapshot if exists
    csv_form = entry_exists_in_csv(selected_employee_id, month_key) or {} if selected_employee_id else {}
    for k, v in csv_form.items():
        form_data.setdefault(k, v)

    employee = None
    if selected_employee_id:
        employee = EmployeeData.query.get(selected_employee_id)

    if employee:
        form_data.setdefault('employee_id', getattr(employee, 'employee_id', selected_employee_id))
        form_data['employee_name'] = employee.employee_name
        form_data.setdefault('id_number', getattr(employee, 'id_number', ''))
        form_data.setdefault('address', getattr(employee, 'address', ''))
        form_data.setdefault('month_result', f"{selected_month}/{selected_year}")

        # Contact & personal info
        form_data.setdefault('city', getattr(employee, 'city', ''))
        form_data.setdefault('postal_code', getattr(employee, 'postal_code', ''))
        form_data.setdefault('phone', getattr(employee, 'phone', ''))
        form_data.setdefault('email', getattr(employee, 'email', ''))
        form_data.setdefault('start_date', getattr(employee, 'start_date', ''))
        form_data.setdefault('date_of_birth', getattr(employee, 'date_of_birth', ''))

        # Bank details
        form_data.setdefault('bank_number', getattr(employee, 'bank_number', ''))
        form_data.setdefault('branch_number', getattr(employee, 'branch_number', ''))
        form_data.setdefault('account_number', getattr(employee, 'account_number', ''))

        # Salary & benefits
        form_data.setdefault('hourly_rate', getattr(employee, 'hourly_rate', 0))
        form_data.setdefault('total_work_days', getattr(employee, 'total_work_days', 0))
        form_data.setdefault('totals_lunch_value', getattr(employee, 'totals_lunch_value', 0))
        form_data.setdefault('total_missing_hours', getattr(employee, 'total_missing_hours', 0))
        form_data.setdefault('mobile_value', getattr(employee, 'mobile_value', 0))
        form_data.setdefault('clothing_value', getattr(employee, 'clothing_value', 0))
        form_data.setdefault('lunch_value', getattr(employee, 'lunch_value', 0))
        form_data.setdefault('cars_value', getattr(employee, 'cars_value', 0))
        form_data.setdefault('advance_payment_salary', getattr(employee, 'advance_payment_salary', 0))
        form_data.setdefault('monthly_city_tax_tops', getattr(employee, 'monthly_city_tax_tops', 0))
        form_data.setdefault('city_value_percentage', getattr(employee, 'city_value_percentage', 0))
        form_data.setdefault('final_city_tax_benefit', getattr(employee, 'final_city_tax_benefit', 0))

        # Salary breakdown
        form_data.setdefault('basic_salary', getattr(employee, 'basic_salary', 0))
        form_data.setdefault('additional_payments', getattr(employee, 'additional_payments', 0))
        form_data.setdefault('net_value', getattr(employee, 'net_value', 0))
        form_data.setdefault('gross_salary', getattr(employee, 'gross_salary', 0))
        form_data.setdefault('gross_taxable', getattr(employee, 'gross_taxable', 0))

        # Above ceiling
        form_data.setdefault('above_ceiling_value', getattr(employee, 'above_ceiling_value', 0))
        form_data.setdefault('above_ceiling_fund', getattr(employee, 'above_ceiling_fund', 0))
        form_data.setdefault('above_ceiling_compensation', getattr(employee, 'above_ceiling_compensation', 0))

        # Employer contributions
        form_data.setdefault('pension_fund', getattr(employee, 'pension_fund', 0))
        form_data.setdefault('compensation', getattr(employee, 'compensation', 0))
        form_data.setdefault('study_fund', getattr(employee, 'study_fund', 0))
        form_data.setdefault('disability', getattr(employee, 'disability', 0))
        form_data.setdefault('miscellaneous', getattr(employee, 'miscellaneous', 0))
        form_data.setdefault('national_insurance', getattr(employee, 'national_insurance', 0))
        form_data.setdefault('salary_tax', getattr(employee, 'salary_tax', 0))
        form_data.setdefault('total_employer_contributions', getattr(employee, 'total_employer_contributions', 0))
        form_data.setdefault('total_salary_cost', getattr(employee, 'total_salary_cost', 0))

        # Employee contributions
        form_data.setdefault('employee_pension_fund', getattr(employee, 'employee_pension_fund', 0))
        form_data.setdefault('self_employed_pension_fund', getattr(employee, 'self_employed_pension_fund', 0))
        form_data.setdefault('study_fund_deductions', getattr(employee, 'study_fund_deductions', 0))
        form_data.setdefault('miscellaneous_deductions', getattr(employee, 'miscellaneous_deductions', 0))
        form_data.setdefault('national_insurance_deductions', getattr(employee, 'national_insurance_deductions', 0))
        form_data.setdefault('health_insurance_deductions', getattr(employee, 'health_insurance_deductions', 0))
        form_data.setdefault('income_tax', getattr(employee, 'income_tax', 0))
        form_data.setdefault('income_tax_before_credit', getattr(employee, 'income_tax_before_credit', 0))
        form_data.setdefault('tax_credit_points', getattr(employee, 'tax_credit_points', 0))
        form_data.setdefault('amount_tax_credit_points_monthly', getattr(employee, 'amount_tax_credit_points_monthly', 0))
        form_data.setdefault('tax_level_precente', getattr(employee, 'tax_level_precente', 0))
        form_data.setdefault('total_salary_pension_funds', getattr(employee, 'total_salary_pension_funds', 0))
        form_data.setdefault('total_deductions', getattr(employee, 'total_deductions', 0))
        form_data.setdefault('net_payment', getattr(employee, 'net_payment', 0))

        # Yearly values
        form_data.setdefault('employee_pension_fund_yearly', getattr(employee, 'employee_pension_fund_yearly', 0))
        form_data.setdefault('self_employed_pension_fund_yearly', getattr(employee, 'self_employed_pension_fund_yearly', 0))
        form_data.setdefault('study_fund_deductions_yearly', getattr(employee, 'study_fund_deductions_yearly', 0))
        form_data.setdefault('miscellaneous_deductions_yearly', getattr(employee, 'miscellaneous_deductions_yearly', 0))
        form_data.setdefault('national_insurance_deductions_yearly', getattr(employee, 'national_insurance_deductions_yearly', 0))
        form_data.setdefault('health_insurance_deductions_yearly', getattr(employee, 'health_insurance_deductions_yearly', 0))
        form_data.setdefault('income_tax_yearly', getattr(employee, 'income_tax_yearly', 0))
        form_data.setdefault('amount_tax_credit_points_monthly_yearly', getattr(employee, 'amount_tax_credit_points_monthly_yearly', 0))
        form_data.setdefault('final_city_tax_benefit_yearly', getattr(employee, 'final_city_tax_benefit_yearly', 0))
        form_data.setdefault('pension_fund_yearly', getattr(employee, 'pension_fund_yearly', 0))
        form_data.setdefault('compensation_yearly', getattr(employee, 'compensation_yearly', 0))
        form_data.setdefault('study_fund_yearly', getattr(employee, 'study_fund_yearly', 0))
        form_data.setdefault('disability_yearly', getattr(employee, 'disability_yearly', 0))
        form_data.setdefault('miscellaneous_yearly', getattr(employee, 'miscellaneous_yearly', 0))
        form_data.setdefault('national_insurance_yearly', getattr(employee, 'national_insurance_yearly', 0))
        form_data.setdefault('salary_tax_yearly', getattr(employee, 'salary_tax_yearly', 0))
        form_data.setdefault('total_employer_contributions_yearly', getattr(employee, 'total_employer_contributions_yearly', 0))
        form_data.setdefault('total_salary_cost_yearly', getattr(employee, 'total_salary_cost_yearly', 0))
        form_data.setdefault('sick_days_salary_yearly', getattr(employee, 'sick_days_salary_yearly', 0))
        form_data.setdefault('vacation_days_salary_yearly', getattr(employee, 'vacation_days_salary_yearly', 0))
        form_data.setdefault('sick_days_balance_yearly', getattr(employee, 'sick_days_balance_yearly', 0))
        form_data.setdefault('vacation_balance_yearly', getattr(employee, 'vacation_balance_yearly', 0))
        form_data.setdefault('gross_taxable_yearly', getattr(employee, 'gross_taxable_yearly', 0))
        
        # Other info
        form_data.setdefault('thirteenth_salary', getattr(employee, 'thirteenth_salary', 0))
        form_data.setdefault('work_percent', getattr(employee, 'work_percent', 0))
        form_data.setdefault('sick_days_salary', getattr(employee, 'sick_days_salary', 0))
        form_data.setdefault('vacation_days_salary', getattr(employee, 'vacation_days_salary', 0))
        form_data.setdefault('sick_days_entitlement', getattr(employee, 'sick_days_entitlement', 0))
        form_data.setdefault('vacation_days_entitlement', getattr(employee, 'vacation_days_entitlement', 0))
        form_data.setdefault('final_extra_hours_weekend', getattr(employee, 'final_extra_hours_weekend', 0))
        form_data.setdefault('final_extra_hours_regular', getattr(employee, 'final_extra_hours_regular', 0))
        form_data.setdefault('food_break_unpaid_salary', getattr(employee, 'food_break_unpaid_salary', 0))
        form_data.setdefault('hours125_regular_salary', getattr(employee, 'hours125_regular_salary', 0))
        form_data.setdefault('hours150_regular_salary', getattr(employee, 'hours150_regular_salary', 0))
        form_data.setdefault('hours150_holidays_saturday_salary', getattr(employee, 'hours150_holidays_saturday_salary', 0))
        form_data.setdefault('hours175_holidays_saturday_salary', getattr(employee, 'hours175_holidays_saturday_salary', 0))
        form_data.setdefault('hours200_holidays_saturday_salary', getattr(employee, 'hours200_holidays_saturday_salary', 0))
        form_data.setdefault('employee_number', getattr(employee, 'employee_number', ''))
        form_data.setdefault('marital_status', getattr(employee, 'marital_status', ''))
        form_data.setdefault('work_apartment', getattr(employee, 'work_apartment', ''))
        form_data.setdefault('hospital', getattr(employee, 'hospital', ''))
        form_data.setdefault('social_number', getattr(employee, 'social_number', ''))
        form_data.setdefault('irs_status', getattr(employee, 'irs_status', ''))
        form_data.setdefault('contract_status', getattr(employee, 'contract_status', ''))
        form_data.setdefault('tax_credit_points', getattr(employee, 'tax_credit_points', ''))
        form_data.setdefault('tax_point_child', getattr(employee, 'tax_point_child', ''))
        form_data.setdefault('message', getattr(employee, 'message', ''))

    # Merge totals from hours_table
    form_data.update(hours_table.get('monthly_totals', {}))
    form_data.update(hours_table.get('paid_totals', {}))
    form_data.update(hours_table.get('tax', {}))

    # Ensure basic fields exist
    form_data.setdefault('employee_id', selected_employee_id)
    form_data.setdefault('employee_name', form_data.get('employee_name', ''))
    form_data.setdefault('id_number', form_data.get('id_number', ''))
    form_data.setdefault('month_result', f"{selected_month}/{selected_year}")

    # Save back into session
    session['form_data'] = form_data
    session['hours_table'] = hours_table

    return render_template(
        'index.html',
        form_data=form_data,
        hours_table=hours_table,
        employee_data=session.get('employee_data', {}),
        selected_employee_id=selected_employee_id,
        employeeMonth=selected_month,
        employeeYear=selected_year,
        month_result=session.get('month_result', ''),
        months=months,
        years=years,
        employees=employees,
        days_data=get_days_in_month(int(selected_year), int(selected_month)),
        employee_details=get_employee_details(selected_employee_id, selected_month, selected_year) if selected_employee_id else {},
        all_hours=json.dumps(load_hours(selected_year), ensure_ascii=False)
    )

# ----------------------
#  Save Table Hours Calculate Data on Page
# ----------------------


@app.route('/save_hours', methods=['POST'])
@login_required
def save_hours_route():
    try:
        today = datetime.today()
        default_month = f"{today.month:02d}"
        default_year = str(today.year)

        data = request.get_json()
        employee_id = str(data.get('employee_id', '')).strip()
        employee_name = data.get('employee_name', '').strip()
        month = str(data.get('month', default_month)).zfill(2)
        year = str(data.get('year', default_year)).strip()

        hours_table = data.get('hours_table', {}) or {}
        work_day_entries_raw = hours_table.get('work_day_entries', []) or []
        monthly_totals_raw = hours_table.get('monthly_totals', {}) or {}
        paid_totals_raw = hours_table.get('paid_totals', {}) or {}
        tax_data_raw = hours_table.get('tax', {}) or {}

        if not work_day_entries_raw:
            return jsonify(success=False, message="אין נתונים לשמירה"), 400

        month_key = f"{year}-{month}"

        # kebab → snake
        def snake(d):
            return {k.replace("-", "_"): v for k, v in d.items()}

        work_day_entries = [snake(e) for e in work_day_entries_raw]
        monthly_totals = snake(monthly_totals_raw)
        paid_totals = snake(paid_totals_raw)
        tax_data = snake(tax_data_raw)

        # === YEARLY TOTALS ===
        def clean_number(value):
            try:
                return float(str(value).replace("₪", "").replace(",", "").strip())
            except:
                return 0.0

        def compute_yearly_totals(all_hours, employee_id, year, current_month, current_tax):

            yearly_fields = [
                "sick_days_salary",
                "vacation_days_salary",
                "sick_days_balance",
                "vacation_balance",
                "gross_taxable",
                "employee_pension_fund",
                "self_employed_pension_fund",
                "study_fund_deductions",
                "miscellaneous_deductions",
                "national_insurance_deductions",
                "health_insurance_deductions",
                "income_tax",
                "amount_tax_credit_points_monthly",
                "final_city_tax_benefit",
                "pension_fund",
                "compensation",
                "study_fund",
                "disability",
                "miscellaneous",
                "national_insurance",
                "salary_tax",
                "total_employer_contributions",
                "total_salary_cost"
            ]

            sick_days_entitlement = 18
            vacation_days_entitlement = 12

            totals = {f"{field}_yearly": 0.0 for field in yearly_fields}

            employee_id = str(employee_id)
            employee_data = all_hours.get(employee_id, {})

            for month_key, month_data in employee_data.items():
                if month_key == "employee_name":
                    continue
                if not month_key.startswith(str(year)):
                    continue

                try:
                    mk_month = int(month_key.split("-")[1])
                except:
                    continue

                if mk_month >= int(current_month):
                    continue

                tax = month_data.get("hours_table", {}).get("tax", {})

                for field in yearly_fields:
                    val = clean_number(tax.get(field, 0))
                    totals[f"{field}_yearly"] += val

            for field in yearly_fields:
                val = clean_number(current_tax.get(field, 0))
                totals[f"{field}_yearly"] += val

            sick_days_used = totals.get("sick_days_salary_yearly", 0.0)
            vacation_days_used = totals.get("vacation_days_salary_yearly", 0.0)

            totals["sick_days_balance_yearly"] = sick_days_entitlement - sick_days_used
            totals["vacation_balance_yearly"] = vacation_days_entitlement - vacation_days_used

            def format_number(val):
                return f"{val:.2f}"

            def format_currency(val):
                return f"{val:,.2f}"

            formatted_totals = {}
            for k, v in totals.items():
                if "balance" in k or "days" in k:
                    formatted_totals[k] = format_number(v)
                else:
                    formatted_totals[k] = format_currency(v)

            return formatted_totals

        # === JSON SAVE ===
        all_hours = load_hours(year) or {}
        all_hours.setdefault(employee_id, {})
        all_hours[employee_id]["employee_name"] = employee_name

        yearly = compute_yearly_totals(all_hours, employee_id, year, month, tax_data_raw)
        tax_data.update(snake(yearly))
        tax_data_raw.update(yearly)

        all_hours[employee_id][month_key] = {
            "hours_table": {
                "work_day_entries": work_day_entries_raw,
                "monthly_totals": monthly_totals_raw,
                "paid_totals": paid_totals_raw,
                "tax": tax_data_raw
            }
        }

        save_hours(all_hours, year)

        # === UPDATE SESSION ===
        session['hours_table'] = all_hours[employee_id][month_key]["hours_table"]
        session['employee_data'] = {
            **monthly_totals_raw,
            **paid_totals_raw,
            **tax_data_raw
        }

        # === BUILD CSV COLUMN ORDER ===

        # 1. base columns
        fieldnames = [
            "employee_id", "employee_name", "month", "section",
            "day", "date", "saturday", "holiday"
        ]

        # 2. daily fields
        for f in [
            'start_time','end_time','hours_calculated','hours_calculated_regular_day',
            'total_extra_hours_regular_day','extra_hours125_regular_day',
            'extra_hours150_regular_day','hours_holidays_day',
            'extra_hours150_holidays_saturday','extra_hours175_holidays_saturday',
            'extra_hours200_holidays_saturday','sick_day','day_off','food_break',
            'final_totals_hours','calc1','calc2','calc3','work_day',
            'missing_work_day','advance_payment'
        ]:
            fieldnames.append(f)

        # 3. monthly fields (snake_case)
        for f in [
                "hours_calculated_monthly",
                "hours_calculated_regular_day_monthly",
                "total_extra_hours_regular_day_monthly",
                "extra_hours125_regular_day_monthly",
                "extra_hours150_regular_day_monthly",
                "hours_holidays_day_monthly",
                "extra_hours150_holidays_saturday_monthly",
                "extra_hours175_holidays_saturday_monthly",
                "extra_hours200_holidays_saturday_monthly",
                "sick_day_monthly",
                "day_off_monthly",
                "food_break_monthly",
                "final_totals_hours_monthly",
                "calc1_monthly",
                "calc2_monthly",
                "calc3_monthly",
                "work_day_monthly",
                "missing_work_day_monthly",
                "advance_payment_monthly"
        ]:
                fieldnames.append(f)

        # 4. paid fields (snake_case)
        for f in [
                "hours_calculated_paid",
                "hours_calculated_regular_day_paid",
                "total_extra_hours_regular_day_paid",
                "extra_hours125_regular_day_paid",
                "extra_hours150_regular_day_paid",
                "hours_holidays_day_paid",
                "extra_hours150_holidays_saturday_paid",
                "extra_hours175_holidays_saturday_paid",
                "extra_hours200_holidays_saturday_paid",
                "sick_day_paid",
                "day_off_paid",
                "food_break_unpaid",
                "final_totals_hours_paid",
                "calc1_paid",
                "calc2_paid",
                "calc3_paid",
                "final_totals_lunch_value_paid",
                "final_total_extra_hours_weekend_monthly",
                "advance_payment_paid"
        ]:
                fieldnames.append(f)

        # 5. tax fields
        for f in tax_data.keys():
            fieldnames.append(f)

        # remove duplicates but keep order
        fieldnames = list(dict.fromkeys(fieldnames))

        # === REBUILD CSV ===
        rows = []

        for emp_id, emp_data in all_hours.items():
            if emp_id == "employee_name": continue
            emp_name = emp_data.get("employee_name", "")

            for mk, mdata in emp_data.items():
                if mk == "employee_name": continue

                tbl = mdata["hours_table"]
                wd = [snake(e) for e in tbl["work_day_entries"]]
                mt = snake(tbl["monthly_totals"])
                pt = snake(tbl["paid_totals"])
                tx = snake(tbl["tax"])

                wrote_summary = False

                for entry in wd:
                    row = {
                        "employee_id": emp_id if not wrote_summary else "",
                        "employee_name": emp_name if not wrote_summary else "",
                        "month": mk if not wrote_summary else "",
                        "section": "daily",
                        "day": entry.get("day", ""),
                        "date": entry.get("date", ""),
                        "saturday": entry.get("saturday", ""),
                        "holiday": entry.get("holiday", "")
                    }

                    # daily fields
                    for k, v in entry.items():
                        if k not in ("day","date","saturday","holiday"):
                            row[k] = v

                    if not wrote_summary:
                        row.update(mt)
                        row.update(pt)
                        row.update(tx)
                        wrote_summary = True
                    else:
                        for k in mt.keys(): row[k] = ""
                        for k in pt.keys(): row[k] = ""
                        for k in tx.keys(): row[k] = ""

                    rows.append(row)

        # === CREATE MAIN FOLDER  ===
        base_dir = os.path.join(app.root_path, "hours_data")           
        os.makedirs(base_dir, exist_ok=True)

        # === CREATE YEAR FOLDER ===
        year_folder = os.path.join(base_dir, f"hours_data_{year}")
        os.makedirs(year_folder, exist_ok=True)

        # === SAVE CSV  ===
        csv_path = os.path.join(year_folder, f"hours_data_{year}.csv")
        with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)

        # === SAVE XLSX  ===
        xlsx_path = os.path.join(year_folder, f"hours_data_{year}.xlsx")
        save_to_csv_and_xlsx(csv_path, xlsx_path)

        # === SAVE JSON  ===
        json_path = os.path.join(year_folder, f"hours_data_{year}.json")
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(all_hours, jf, ensure_ascii=False, indent=2)

        return jsonify(success=True, message="הנתונים נשמרו בהצלחה")

    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

# ----------------------
#  Save To Csv And Xlsx All Data On Folder
# ----------------------

def save_to_csv_and_xlsx(csv_path, xlsx_path):
    if not os.path.exists(csv_path):
        return  # nothing to export yet

    # Load the CSV into pandas
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    
    # Save as Excel (XLSX)
    with pd.ExcelWriter(xlsx_path, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Hours')
        
        # Access the workbook and worksheet
        workbook  = writer.book
        worksheet = writer.sheets['Hours']

        # Freeze the first row
        worksheet.freeze_panes(1, 0)

        # Set RTL Hebrew View
        worksheet.right_to_left()

        # Auto-adjust column widths
        for i, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, max_len)

        # === Define formats ===
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#000000',   # black background
            'font_color': '#FFFFFF', # white text
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })

        body_format = workbook.add_format({
            'border': 1,
            'border_color': '#FFFFFF',  # white grid lines
            'bg_color': '#D9EAF7'       # light blue background
        })

        alt_body_format = workbook.add_format({
            'border': 1,
            'border_color': '#FFFFFF',
            'bg_color': '#F2F2F2'       # light gray alternate rows
        })

        # === Apply header format ===
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)

        # === Apply body formats (striped rows) ===
        for row_num in range(1, len(df) + 1):
            fmt = body_format if row_num % 2 else alt_body_format
            worksheet.set_row(row_num, None, fmt)

# ----------------------
# Get Hours Data: Form Page
# ----------------------
def normalize_keys(data_dict):
    """Convert snake_case keys to kebab-case for frontend."""
    if not isinstance(data_dict, dict):
        return {}
    return {k.replace("_", "-"): v for k, v in data_dict.items()}




@app.route('/get_hours_data')
@login_required
def get_hours_data():
    employee_id = session.get('employee_id')
    selected_year = session.get('selected_year')
    selected_month = session.get('selected_month')

    if not employee_id or not selected_year or not selected_month:
        return jsonify({"empty": True})

    selected_month_str = str(selected_month).zfill(2)
    selected_year_str = str(selected_year)

    month_key = f"{selected_year_str}-{selected_month_str}"

    all_hours = load_hours(selected_year) or {}

    employee_data = all_hours.get(str(employee_id), {})
    month_data = employee_data.get(month_key, {})

    hours_table = month_data.get("hours_table", {})

    work_day_entries = hours_table.get("work_day_entries", [])
    monthly_totals = hours_table.get("monthly_totals", {})
    paid_totals = hours_table.get("paid_totals", {})
    tax_data = hours_table.get("tax", {})

    #  If no saved hours → return empty
    if not work_day_entries:
        return jsonify({"empty": True})

    # Normalize
    work_day_entries = [normalize_keys(entry) for entry in work_day_entries]
    monthly_totals = normalize_keys(monthly_totals)
    paid_totals = normalize_keys(paid_totals)
    tax_data = normalize_keys(tax_data)

    return jsonify({
        "empty": False,
        "work_day_entries": work_day_entries,
        "monthly_totals": monthly_totals,
        "paid_totals": paid_totals,
        "tax": tax_data
    })

# --------------------
# Clear Employee Form Data
# ----------------------

@app.route('/clear_display', methods=['POST'])
@login_required
def clear_data():
    session.pop('employee_id', None)
    session.pop('selected_month', None)
    session.pop('selected_year', None)
    session.pop('employee_data', None)
    session.pop('hours_table', None)
    session.pop('month_result', None)
    session.pop('form_data', None)

    flash("הטופס נוקה בהצלחה", "info")
    return redirect(url_for('index'))

# --------------------
# Conected To Tax Office To Ger Recive Data Permission Invoice Number Data
# ----------------------

IRS_API_URL = "https://api.misim.gov.il/invoices"  # כתובת לדוגמה, בפועל תקבל מהרשות

def send_invoice_to_tax_authority(invoice_data):
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer YOUR_API_TOKEN"  # טוקן שתקבל מרשות המיסים
    }
    response = requests.post(IRS_API_URL, headers=headers, data=json.dumps(invoice_data))
    
    if response.status_code == 200:
        result = response.json()
        allocation_number = result.get("allocation_number")
        return allocation_number
    else:
        raise Exception(f"Tax API error: {response.status_code} {response.text}")

# --------------------
# Send Permission Invoice Number Data
# ----------------------

@app.route("/send_invoice", methods=["POST"])
@login_required
def send_invoice():
    data = request.get_json()
    invoice_id = data.get("invoice_id")

    # שליפת נתוני החשבונית מהמערכת שלך
    invoice_data = get_invoice_data(invoice_id)

    # שליחה לרשות המיסים
    try:
        allocation_number = send_invoice_to_tax_authority(invoice_data)
        return jsonify({"status": "success", "allocation_number": allocation_number})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# --------------------
#  Invoice Form Data
# ----------------------

@app.route('/invoice')
@login_required
def view_invoice():
    # שליפת כל המוצרים מה-DB
    products_db = Product.query.all()
    products_list_for_js = [product.to_dict() for product in products_db]

    #  Load company data from JSON
    company = load_company_data()

    invoice_data = {
        'invoice_number': 'INV-2025-12345',
        'invoice_date': datetime.today().strftime('%Y-%m-%d'),
        'client_name': 'לקוח לדוגמה בע"מ',
        'client_address': 'רחוב הרצל 1, תל אביב',
        'client_id': '558765432',
        'items': [
            {'description': 'שירותי פיתוח תוכנה', 'quantity': 2, 'unit_price': 500.00, 'total': 1000.00},
            {'description': 'תחזוקה חודשית', 'quantity': 1, 'unit_price': 200.00, 'total': 200.00},
        ],
        'sub_total': 1200.00,
        'vat_rate': 17,
        'vat_amount': 204.00,
        'grand_total': 1404.00,
        'allocation_number': '202511300000001',
        'inventory_items': products_list_for_js,
        'vat_options': [15, 16, 17, 18, 19],
        #  pass company data into template
        'company': company
    }

    return render_template('invoice.html', **invoice_data)


@app.route('/invoice_dynamic')
@login_required
def view_invoice_dynamic():
    # שליפת כל המוצרים מה-DB
    products_db = Product.query.all()
    products_list_for_js = [product.to_dict() for product in products_db]

    invoice_data = {
        'invoice_number': 'INV-2025-12346',
        'invoice_date': datetime.today().strftime('%Y-%m-%d'),
        'business_id': '551234567',
        'client_name': 'לקוח לדוגמה בע"מ',
        'client_address': 'רחוב הרצל 1, תל אביב',
        'client_id': '558765432',
        'sub_total': 0.00,
        'grand_total': 0.00,
        'allocation_number': 'טרם הוקצה',
        'inventory_items': products_list_for_js, # ✅ שימוש ברשימה מה-DB
        'vat_options': [15, 16, 17, 18, 19]
    }

    return render_template('invoice_dynamic.html', **invoice_data)

# --------------------
#  Products Manage Form Data
# ----------------------

@app.route('/products_manage', methods=['GET', 'POST'])
@login_required
def manage_products():
    if request.method == 'POST':
        product_name = request.form.get('name')
        product_price = request.form.get('price')
        product_description = request.form.get('description')

        if product_name and product_price:
            new_product = Product(
                name=product_name, 
                price=float(product_price), 
                description=product_description
            )
            db.session.add(new_product)
            db.session.commit()
            # ניתן להוסיף כאן הודעת פלאש על הצלחה
        
        # ניתן להוסיף כאן טיפול במחיקה/עדכון אם תרצה בעתיד

    # שליפת כל המוצרים מה-DB עבור התצוגה
    products = Product.query.all()
    return render_template('products_manage.html', products=products)

# --------------------
#  Products Delete Selected Form Data
# ----------------------

@app.route('/delete_selected_products', methods=['POST'])
@login_required
def delete_selected_products():
    # Get the list of product IDs from the checkboxes named "delete_products"
    selected_product_ids = request.form.getlist('delete_products')

    if not selected_product_ids:
        flash("לא נבחרו מוצרים למחיקה", "warning")
        # Redirect back to the product management page
        return redirect(url_for('manage_products')) 

    try:
        # Convert the list of string IDs from the form into a list of integers
        product_ids_int = [int(p_id) for p_id in selected_product_ids]
        
        # Use SQLAlchemy to delete all products whose IDs are in the list
        Product.query.filter(Product.id.in_(product_ids_int)).delete(synchronize_session=False)
        
        # Commit the changes to the database
        db.session.commit()
        
        flash(f"✅ נמחקו {len(selected_product_ids)} מוצרים", "success")
        return redirect(url_for('manage_products')) # Redirect back to the product management page

    except Exception as e:
        db.session.rollback()
        flash(f"שגיאה בעת מחיקת מוצרים: {str(e)}", "danger")
        # Ensure 'manage_products' is the endpoint name of your route function
        return redirect(url_for('manage_products')) 




# --------------------
#  Form 102 Form Data
# ----------------------

@app.route('/form_102', methods=['GET', 'POST'])
@login_required
def form_102():
    employees = EmployeeData.query.all()
    company_data = load_company_data()

    # ----- בסיס זמן -----
    now = datetime.now()
    months = range(1, 13)
    years = range(now.year - 2, now.year + 2)

    #  POST — שמירת נתונים
    if request.method == 'POST':

        new_employee_id = request.form.get('employee_id')
        old_employee_id = session.get('employee_id')

        #  אם המשתמש החליף עובד בתוך הטופס → ננקה לפני טעינה מחדש
        if new_employee_id != old_employee_id:
            session['form_data'] = {}
            session['employee_id'] = new_employee_id
            return redirect(url_for('form_102'))

        #  שמירת חודש/שנה
        if request.form.get('reportMonth'):
            session['selected_month'] = int(request.form.get('reportMonth'))
        if request.form.get('reportYear'):
            session['selected_year'] = int(request.form.get('reportYear'))

        #  שמירת נתוני עובד
        employee = EmployeeData.query.get(new_employee_id)
        if employee:
            for form_field, model_attrs in FIELD_MAP_102.items():
                if form_field in request.form:
                    value = request.form.get(form_field)
                    for attr in model_attrs:
                        if hasattr(employee, attr):
                            setattr(employee, attr, value)
            db.session.commit()

        #  שמירת נתוני הטופס ב-session
        session['form_data'] = request.form.to_dict()

        flash('נתוני טופס 102 עודכנו בהצלחה!', 'success')
        return redirect(url_for('form_102'))

    #  GET — קריאת פרמטרים מה-URL או מה-session
    selected_employee_id = request.args.get('employee_id') or session.get('employee_id', '')
    selected_month = request.args.get('month')
    selected_year = request.args.get('year')

    selected_month = int(selected_month) if selected_month else int(session.get('selected_month', now.month))
    selected_year = int(selected_year) if selected_year else int(session.get('selected_year', now.year))

    #  ניקוי טופס 102 לפי בקשה מפורשת
    if session.pop('clear_102', None):
        return render_template(
            'form_102.html',
            form_data={},
            employees=employees,
            employee_data={},
            selected_employee_id='',
            time=time,
            employeeMonth='',
            employeeYear='',
            months=months,
            years=years
        )

    #  זיהוי שינוי עובד / חודש / שנה
    previous_employee_id = session.get('employee_id')
    previous_month = session.get('selected_month')
    previous_year = session.get('selected_year')

    employee_changed = previous_employee_id and selected_employee_id and previous_employee_id != selected_employee_id
    month_changed = previous_month and selected_month and int(previous_month) != int(selected_month)
    year_changed = previous_year and selected_year and int(previous_year) != int(selected_year)

    #  אם משהו השתנה → ננקה רק את נתוני הטופס
    if employee_changed or month_changed or year_changed:
        session['form_data'] = {}

    #  עדכון ה-session לערכים החדשים
    session['employee_id'] = selected_employee_id
    session['selected_month'] = selected_month
    session['selected_year'] = selected_year

    #  אם אין form_data — אל תחשב totals, תחזיר טופס ריק
    if not session.get('form_data'):
        return render_template(
            'form_102.html',
            form_data={},
            employees=employees,
            employee_data={},
            selected_employee_id=session.get('employee_id', ''),
            time=time,
            employeeMonth=selected_month,
            employeeYear=selected_year,
            months=months,
            years=years
        )

    #  AJAX GET — שליפת נתוני עובד
    if request.method == 'GET' and request.args.get('action') == 'get_employee_data':
        employee_id = request.args.get('employee_id')
        m = request.args.get('month') or selected_month
        y = request.args.get('year') or selected_year
        details = get_employee_details(employee_id, m, y)
        return jsonify({'success': bool(details), **(details or {})})

    #  חישוב totals
    form_data = session.get('form_data', {})
    all_hours = load_hours(selected_year) or {}

    employee_count = 0
    total_gross = 0.0
    total_income_tax = 0.0
    total_ni_employee = 0.0
    total_health = 0.0
    total_study_fund_deductions = 0.0

    emp_pension = 0.0
    self_pension = 0.0

    pension_val = 0.0
    comp_val = 0.0
    disability_val = 0.0
    study_fund_val = 0.0

    regular_salary = 0.0
    reduced_salary = 0.0
    regular_count = 0
    reduced_count = 0

    month_key = f"{selected_year}-{str(selected_month).zfill(2)}"

    # Clean Number helper
    def cn(val):
        try:
            return float(str(val).replace("₪", "").replace(",", "").strip())
        except:
            return 0.0

    for emp_id, emp_months in all_hours.items():
        if month_key in emp_months:
            employee_count += 1

            tax_data = emp_months[month_key].get("hours_table", {}).get("tax", {})

            gross_taxable = cn(tax_data.get("gross_taxable", 0))
            dob = tax_data.get("date_of_birth") or None

            #  חישוב שכר רגיל / מופחת לפי גיל
            if dob:
                try:
                    birth = datetime.strptime(dob, "%Y-%m-%d")
                    today = datetime.today()
                    age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
                except:
                    age = 0
            else:
                age = 0

            if age < 18 or age >= 67:
                reduced_salary += gross_taxable
                reduced_count += 1
            else:
                regular_salary += gross_taxable
                regular_count += 1

            total_gross += gross_taxable
            total_income_tax += cn(tax_data.get("income_tax", 0))
            total_ni_employee += cn(tax_data.get("national_insurance_deductions", 0))
            total_health += cn(tax_data.get("health_insurance_deductions", 0))
            total_study_fund_deductions += cn(tax_data.get("study_fund_deductions", 0))

            emp_pension += cn(tax_data.get("employee_pension_fund", 0))
            self_pension += cn(tax_data.get("self_employed_pension_fund", 0))

            pension_val += cn(tax_data.get("pension_fund", 0))
            comp_val += cn(tax_data.get("compensation", 0))
            disability_val += cn(tax_data.get("disability", 0))
            study_fund_val += cn(tax_data.get("study_fund", 0))

    final_emp_pension_combined = emp_pension + self_pension

    final_emp_deductions_total = (
        total_ni_employee +
        total_health +
        final_emp_pension_combined +
        total_study_fund_deductions
    )

    total_employer_pension_combined = (
        pension_val +
        comp_val +
        disability_val +
        study_fund_val
    )

    final_totals_paid = (
        final_emp_deductions_total +
        total_employer_pension_combined
    )

    final_totals_income_tax = total_income_tax

    form_data.update({
        'NumEmployees': employee_count,
        'regular_salary_hidden': round_form_number(regular_salary),
        'reduced_salary_hidden': round_form_number(reduced_salary),
        'regular_count_hidden': regular_count,
        'reduced_count_hidden': reduced_count,
        'total_salary_hidden': round_form_number(regular_salary + reduced_salary),
         
        'totalGrossSalary': round_form_number(total_gross),
        'totalIncomeTax': round_form_number(total_income_tax),
        'totalNationalInsurance': round_form_number(total_ni_employee),
        'totalHealthInsurance': round_form_number(total_health),
        'totalProvidentDeduction': round_form_number(total_study_fund_deductions),

        'totalEmpPension': round_form_number(emp_pension),
        'totalSelfPension': round_form_number(self_pension),
        'totalPensionDeduction':round_form_number(final_emp_pension_combined),

        'totalPensionVal': round_form_number(pension_val),
        'totalCompVal': round_form_number(comp_val),
        'totalDisabilityVal': round_form_number(disability_val),
        'totalStudyFundVal': round_form_number(study_fund_val),
        'employerPension': round_form_number(total_employer_pension_combined),

        'totalEmpDeductions': round_form_number(final_emp_deductions_total),
        'finalTotalsPaid': round_form_number(final_totals_paid),
        'finalTotalIncomeTax': round_form_number(final_totals_income_tax),

        'reportMonth': selected_month,
        'reportYear': selected_year
    })

    form_data.setdefault("companyName", company_data.get("name", ""))
    form_data.setdefault("taxFileNumber", company_data.get("תיק ניכויים", ""))
    form_data.setdefault("companyAddress", company_data.get("address", ""))

    session["form_data"] = form_data

    return render_template(
        'form_102.html',
        form_data=form_data,
        employees=employees,
        employee_data=session.get('employee_data', {}),
        selected_employee_id=session.get('employee_id', ''),
        time=time,
        employeeMonth=selected_month,
        employeeYear=selected_year,
        months=months,
        years=years
    )



@app.route('/submit102', methods=['POST'])
def submit_form_102():
    data = request.form.to_dict()
    return jsonify(data)

# --------------------
# Save Form 102 Data 
# ---------------------- 

@app.route('/save_form_102', methods=['POST'])
@login_required
def save_form_102():
    try:
        data = request.get_json() or {}

        # 1) קריאת פרמטרים בסיסיים
        employee_id = str(data.get("employee_id", "")).strip()
        employee_name = data.get("employee_name", "").strip()
        month = str(data.get("reportMonth", "")).zfill(2)
        year = str(data.get("reportYear", ""))

        if not employee_id or not month or not year:
            return jsonify(success=False, message="חסרים פרמטרים לשמירה"), 400

        month_key = f"{year}-{month}"

        # === 2) יצירת תיקייה ראשית form_102 ===
        base_dir = os.path.join(app.root_path, "form_102")
        os.makedirs(base_dir, exist_ok=True)

        # === 3) יצירת תיקייה לפי שנה ===
        year_folder = os.path.join(base_dir, f"102_{year}")
        os.makedirs(year_folder, exist_ok=True)

        # === 4) שמירה ל־JSON לפי חודש ===
        json_path = os.path.join(year_folder, f"102_{month}_{year}.json")

        # טוען קובץ קיים אם יש
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                month_data = json.load(f)
        else:
            month_data = {}

        # עדכון נתוני העובד
        month_data[employee_id] = {
            "employee_name": employee_name,
            "form_data": data
        }

        # כתיבה לקובץ JSON
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(month_data, f, ensure_ascii=False, indent=4)

        # === 5) בניית CSV ===
        csv_path = os.path.join(year_folder, f"102_{month}_{year}.csv")

        fieldnames = list(data.keys())

        with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(data)

        # === 6) יצירת XLSX ===
        xlsx_path = os.path.join(year_folder, f"102_{month}_{year}.xlsx")

        df = pd.DataFrame([data])
        save_102_excel(csv_path, xlsx_path)

        # === 7) עדכון session ===
        session["form_102"] = data

        return jsonify(success=True, message="טופס 102 נשמר בהצלחה!")

    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

# ----------------------
#  Save To Csv And Xlsx All Data On Folder Form 102
# ----------------------

def save_102_excel(csv_path, xlsx_path):
    if not os.path.exists(csv_path):
        return

    df = pd.read_csv(csv_path, encoding='utf-8-sig')

    with pd.ExcelWriter(xlsx_path, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Form102')

        workbook  = writer.book
        worksheet = writer.sheets['Form102']

        # Freeze header
        worksheet.freeze_panes(1, 0)

        # RTL
        worksheet.right_to_left()

        # Auto column width
        for i, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, max_len)

        # Header format
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#000000',
            'font_color': '#FFFFFF',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })

        # Body formats
        body_format = workbook.add_format({
            'border': 1,
            'border_color': '#FFFFFF',
            'bg_color': '#D9EAF7'
        })

        alt_body_format = workbook.add_format({
            'border': 1,
            'border_color': '#FFFFFF',
            'bg_color': '#F2F2F2'
        })

        # Apply header
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)

        # Apply striped rows
        for row_num in range(1, len(df) + 1):
            fmt = body_format if row_num % 2 else alt_body_format
            worksheet.set_row(row_num, None, fmt)

# --------------------
#  Save Form 102 Report Data To Folder
# ---------------------- 

@app.route("/save_form102_report", methods=["POST"])
@login_required
def save_form102_report():
    import os, json
    data = request.json

    month = data["employer"]["reportMonth"]
    year = data["employer"]["reportYear"]

    # === יצירת תיקייה ראשית ===
    base_dir = os.path.join(app.root_path, "form_102_report")
    os.makedirs(base_dir, exist_ok=True)

    # === יצירת תיקייה לפי שנה ===
    year_folder = os.path.join(base_dir, f"Form_102_{year}")
    os.makedirs(year_folder, exist_ok=True)

    # === יצירת שמות קבצים ===
    filename_json = f"Form_102_report_{month}_{year}.json"
    filename_xml = f"Form_102_report_{month}_{year}.xml"

    json_path = os.path.join(year_folder, filename_json)
    xml_path = os.path.join(year_folder, filename_xml)

    # === שמירת JSON ===
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # === שמירת XML ===
    xml_content = data["xml"]
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(xml_content)

    return jsonify({
        "success": True,
        "json_file": filename_json,
        "xml_file": filename_xml,
        "folder": year_folder
    })

# --------------------
#   Convert Fields Name From App To Tax Office Name Report Form 102 Form Data
# ----------------------

FIELD_MAP_102 = {

    # ===== פרטי מעסיק =====
    "companyName": ["companyName"],
    "companyAddress": ["companyAddress"],
    "taxFileNumber": ["taxFileNumber"],
    "reportMonth": ["reportMonth"],
    "reportYear": ["reportYear"],

    # ===== שורה 216 =====
    "totalIncomeTax": ["totalIncomeTax"],
    "totalGrossSalary": ["totalGrossSalary"],
    "NumEmployees": ["NumEmployees"],

    # ===== שורה 254 =====
    "totalPensionVal": ["totalPensionVal"],
    "totalCompVal": ["totalCompVal"],
    "NumEmployeesNonSalary": ["NumEmployeesNonSalary"],

    # ===== שורה 291 =====
    "totalEmpDeductions": ["totalEmpDeductions"],
    "totalStudyFundVal": ["totalStudyFundVal"],

    # ===== שורה 329 =====
    "employerPension": ["employerPension"],
    "totalPensionDeduction": ["totalPensionDeduction"],
    "NumEmployeesCharges": ["NumEmployeesCharges"],

    # ===== שורה 367 =====
    "totalNationalInsurance": ["totalNationalInsurance"],
    "totalHealthInsurance": ["totalHealthInsurance"],
    "NumEmployeesCharges2": ["NumEmployeesCharges2"],

    # ===== שורה 404 =====
    "finalTotalIncomeTax": ["finalTotalIncomeTax"],
}


# --------------------
# Send Form 102 To Tax Office Requst Data
# ----------------------

@app.route('/send_102_to_tax', methods=['POST'])
@login_required
def send_102_to_tax():
    if not session.get("owner_access"):
        flash("⛔ רק בעלים יכול לשדר לרשות המיסים.", "danger")
        return redirect(url_for('form_102'))

    # קובץ ה‑XML שנוצר קודם
    xml_path = session.get("generated_xml_path")

    if not xml_path or not os.path.exists(xml_path):
        flash("קובץ XML לא נמצא — צור אותו מחדש.", "danger")
        return redirect(url_for('form_102'))

    # טוען את ה‑XML
    with open(xml_path, "rb") as f:
        xml_data = f.read()

    #  URL דמיוני — אתה תחליף לכתובת האמיתית
    TAX_URL = "https://tax.gov.il/api/102/upload"

    #  תעודה דיגיטלית — אתה תחליף לשם הקובץ שלך
    CERT_FILE = "certs/company_cert.pfx"
    CERT_PASS = "12345678"  # תחליף לסיסמה שלך

    try:
        response = requests.post(
            TAX_URL,
            data=xml_data,
            cert=(CERT_FILE, CERT_PASS),
            headers={"Content-Type": "text/xml"},
            timeout=30
        )

        # שומר את התשובה בתיקייה
        log_path = xml_path.replace(".xml", "_response.xml")
        with open(log_path, "wb") as f:
            f.write(response.content)

        flash("השידור בוצע. התקבלה תשובה מרשות המיסים.", "info")
        return redirect(url_for('form_102'))

    except Exception as e:
        flash(f"שגיאה בשידור: {str(e)}", "danger")
        return redirect(url_for('form_102'))



# --------------------
# Clear Form 102 Data
# ----------------------

@app.route('/clear_form102', methods=['POST'])
@login_required
def clear_form102():
    session['clear_102'] = True
    return redirect(url_for('form_102'))



# --------------------
#  Fix Form 102 Number Format Data
# ----------------------

# ===== עיגול מספרים לפי חוק =====
def round_form_number(val):
    if not val:
        return ""
    try:
        cleaned = str(val).replace(",", "").strip()
        num = float(cleaned)
        return f"{round(num):,}"
    except:
        return ""

# --------------------
#  Form B102 Form Data
# ----------------------

@app.route('/form_B102', methods=['GET', 'POST'])
@login_required
def form_B102():
    employees = EmployeeData.query.all()
    company_data = load_company_data()

    # ----- בסיס זמן -----
    now = datetime.now()
    months = range(1, 13)
    years = range(now.year - 2, now.year + 2)

    #  POST — שמירת נתונים
    if request.method == 'POST':

        new_employee_id = request.form.get('employee_id')
        old_employee_id = session.get('employee_id')

        #  אם המשתמש החליף עובד בתוך הטופס → ננקה לפני טעינה מחדש
        if new_employee_id != old_employee_id:
            session['form_data'] = {}
            session['employee_id'] = new_employee_id
            return redirect(url_for('form_B102'))

        #  שמירת חודש/שנה
        if request.form.get('reportMonth'):
            session['selected_month'] = int(request.form.get('reportMonth'))
        if request.form.get('reportYear'):
            session['selected_year'] = int(request.form.get('reportYear'))

        #  שמירת נתוני עובד
        employee = EmployeeData.query.get(new_employee_id)
        if employee:
            for form_field, model_attrs in FIELD_MAP_B102.items():
                if form_field in request.form:
                    value = request.form.get(form_field)
                    for attr in model_attrs:
                        if hasattr(employee, attr):
                            setattr(employee, attr, value)
            db.session.commit()

        #  שמירת נתוני הטופס ב-session
        session['form_data'] = request.form.to_dict()

        flash('נתוני טופס B102 עודכנו בהצלחה!', 'success')
        return redirect(url_for('form_B102'))

    #  GET — קריאת פרמטרים מה-URL או מה-session
    selected_employee_id = request.args.get('employee_id') or session.get('employee_id', '')
    selected_month = request.args.get('month')
    selected_year = request.args.get('year')

    selected_month = int(selected_month) if selected_month else int(session.get('selected_month', now.month))
    selected_year = int(selected_year) if selected_year else int(session.get('selected_year', now.year))

    #  ניקוי טופס B102 לפי בקשה מפורשת
    if session.pop('clear_B102', None):
        return render_template(
            'form_B102.html',
            form_data={},
            employees=employees,
            employee_data={},
            selected_employee_id='',
            time=time,
            employeeMonth='',
            employeeYear='',
            months=months,
            years=years
        )

    #  זיהוי שינוי עובד / חודש / שנה
    previous_employee_id = session.get('employee_id')
    previous_month = session.get('selected_month')
    previous_year = session.get('selected_year')

    employee_changed = previous_employee_id and selected_employee_id and previous_employee_id != selected_employee_id
    month_changed = previous_month and selected_month and int(previous_month) != int(selected_month)
    year_changed = previous_year and selected_year and int(previous_year) != int(selected_year)

    #  אם משהו השתנה → ננקה רק את נתוני הטופס
    if employee_changed or month_changed or year_changed:
        session['form_data'] = {}

    #  עדכון ה-session לערכים החדשים
    session['employee_id'] = selected_employee_id
    session['selected_month'] = selected_month
    session['selected_year'] = selected_year

    #  אם אין form_data — אל תחשב totals, תחזיר טופס ריק
    if not session.get('form_data'):
        return render_template(
            'form_B102.html',
            form_data={},
            employees=employees,
            employee_data={},
            selected_employee_id=session.get('employee_id', ''),
            time=time,
            employeeMonth=selected_month,
            employeeYear=selected_year,
            months=months,
            years=years
        )

    #  AJAX GET — שליפת נתוני עובד
    if request.method == 'GET' and request.args.get('action') == 'get_employee_data':
        employee_id = request.args.get('employee_id')
        m = request.args.get('month') or selected_month
        y = request.args.get('year') or selected_year
        details = get_employee_details(employee_id, m, y)
        return jsonify({'success': bool(details), **(details or {})})


    #  חישוב totals
    form_data = session.get('form_data', {})
    all_hours = load_hours(selected_year) or {}

    employee_count = 0
    total_gross = 0.0
    total_income_tax = 0.0
    total_ni_employee = 0.0
    total_health = 0.0
    total_study_fund_deductions = 0.0

    emp_pension = 0.0
    self_pension = 0.0

    pension_val = 0.0
    comp_val = 0.0
    disability_val = 0.0
    study_fund_val = 0.0

    regular_salary = 0.0
    reduced_salary = 0.0
    regular_count = 0
    reduced_count = 0

    month_key = f"{selected_year}-{str(selected_month).zfill(2)}"

    # Clean Number helper
    def cn(val):
        try:
            return float(str(val).replace("₪", "").replace(",", "").strip())
        except:
            return 0.0

    for emp_id, emp_months in all_hours.items():
        if month_key in emp_months:
            employee_count += 1

            tax_data = emp_months[month_key].get("hours_table", {}).get("tax", {})

            gross_taxable = cn(tax_data.get("gross_taxable", 0))
            dob = tax_data.get("date_of_birth") or None

            #  חישוב שכר רגיל / מופחת לפי גיל
            if dob:
                try:
                    birth = datetime.strptime(dob, "%Y-%m-%d")
                    today = datetime.today()
                    age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
                except:
                    age = 0
            else:
                age = 0

            if age < 18 or age >= 67:
                reduced_salary += gross_taxable
                reduced_count += 1
            else:
                regular_salary += gross_taxable
                regular_count += 1

            total_gross += gross_taxable
            total_income_tax += cn(tax_data.get("income_tax", 0))
            total_ni_employee += cn(tax_data.get("national_insurance_deductions", 0))
            total_health += cn(tax_data.get("health_insurance_deductions", 0))
            total_study_fund_deductions += cn(tax_data.get("study_fund_deductions", 0))

            emp_pension += cn(tax_data.get("employee_pension_fund", 0))
            self_pension += cn(tax_data.get("self_employed_pension_fund", 0))

            pension_val += cn(tax_data.get("pension_fund", 0))
            comp_val += cn(tax_data.get("compensation", 0))
            disability_val += cn(tax_data.get("disability", 0))
            study_fund_val += cn(tax_data.get("study_fund", 0))

    final_emp_pension_combined = emp_pension + self_pension

    final_emp_deductions_total = (
        total_ni_employee +
        total_health +
        final_emp_pension_combined +
        total_study_fund_deductions
    )

    total_employer_pension_combined = (
        pension_val +
        comp_val +
        disability_val +
        study_fund_val
    )

    final_totals_paid = (
        final_emp_deductions_total +
        total_employer_pension_combined
    )

    final_totals_income_tax = total_income_tax

    form_data.update({
        'NumEmployees': employee_count,
        'regular_salary_hidden': round_form_number(regular_salary),
        'reduced_salary_hidden': round_form_number(reduced_salary),
        'regular_count_hidden': regular_count,
        'reduced_count_hidden': reduced_count,
        'total_salary_hidden': round_form_number(regular_salary + reduced_salary),
         
        'totalGrossSalary': round_form_number(total_gross),
        'totalIncomeTax': round_form_number(total_income_tax),
        'totalNationalInsurance': round_form_number(total_ni_employee),
        'totalHealthInsurance': round_form_number(total_health),
        'totalProvidentDeduction': round_form_number(total_study_fund_deductions),

        'totalEmpPension': round_form_number(emp_pension),
        'totalSelfPension': round_form_number(self_pension),
        'totalPensionDeduction':round_form_number(final_emp_pension_combined),

        'totalPensionVal': round_form_number(pension_val),
        'totalCompVal': round_form_number(comp_val),
        'totalDisabilityVal': round_form_number(disability_val),
        'totalStudyFundVal': round_form_number(study_fund_val),
        'employerPension': round_form_number(total_employer_pension_combined),

        'totalEmpDeductions': round_form_number(final_emp_deductions_total),
        'finalTotalsPaid': round_form_number(final_totals_paid),
        'finalTotalIncomeTax': round_form_number(final_totals_income_tax),

        'reportMonth': selected_month,
        'reportYear': selected_year
    })

    form_data.setdefault("companyName", company_data.get("name", ""))
    form_data.setdefault("taxFileNumber", company_data.get("תיק ניכויים", ""))
    form_data.setdefault("companyAddress", company_data.get("address", ""))

    session["form_data"] = form_data

    return render_template(
        'form_B102.html',
        form_data=form_data,
        employees=employees,
        employee_data=session.get('employee_data', {}),
        selected_employee_id=session.get('employee_id', ''),
        time=time,
        employeeMonth=selected_month,
        employeeYear=selected_year,
        months=months,
        years=years
    )


@app.route('/submitB102', methods=['POST'])
def submit_form_B102():
    data = request.form.to_dict()
    return jsonify(data)


# --------------------
# Save Form B102 Data 
# ----------------------
 
@app.route('/save_form_B102', methods=['POST'])
@login_required
def save_form_B102():
    try:
        data = request.get_json() or {}

        # 1) קריאת פרמטרים בסיסיים
        employee_id = str(data.get("employee_id", "")).strip()
        employee_name = data.get("employee_name", "").strip()
        month = str(data.get("reportMonth", "")).zfill(2)
        year = str(data.get("reportYear", ""))

        if not employee_id or not month or not year:
            return jsonify(success=False, message="חסרים פרמטרים לשמירה"), 400

        month_key = f"{year}-{month}"

        # === 2) יצירת תיקייה ראשית form_B102 ===
        base_dir = os.path.join(app.root_path, "form_B102")
        os.makedirs(base_dir, exist_ok=True)

        # === 3) יצירת תיקייה לפי שנה ===
        year_folder = os.path.join(base_dir, f"B102_{year}")
        os.makedirs(year_folder, exist_ok=True)

        # === 4) שמירה ל־JSON לפי חודש ===
        json_path = os.path.join(year_folder, f"B102_{month}_{year}.json")

        # טוען קובץ קיים אם יש
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                month_data = json.load(f)
        else:
            month_data = {}

        # עדכון נתוני העובד
        month_data[employee_id] = {
            "employee_name": employee_name,
            "form_data": data
        }

        # כתיבה לקובץ JSON
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(month_data, f, ensure_ascii=False, indent=4)

        # === 5) בניית CSV ===
        csv_path = os.path.join(year_folder, f"B102_{month}_{year}.csv")

        fieldnames = list(data.keys())

        with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(data)

        # === 6) יצירת XLSX ===
        xlsx_path = os.path.join(year_folder, f"B102_{month}_{year}.xlsx")

        df = pd.DataFrame([data])
        save_B102_excel(csv_path, xlsx_path)

        # === 7) עדכון session ===
        session["form_B102"] = data

        return jsonify(success=True, message="טופס B102 נשמר בהצלחה!")

    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

# ----------------------
#  Save To Csv And Xlsx All Data On Folder Form B102
# ----------------------

def save_B102_excel(csv_path, xlsx_path):
    if not os.path.exists(csv_path):
        return

    df = pd.read_csv(csv_path, encoding='utf-8-sig')

    with pd.ExcelWriter(xlsx_path, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='FormB102')

        workbook  = writer.book
        worksheet = writer.sheets['FormB102']

        # Freeze header
        worksheet.freeze_panes(1, 0)

        # RTL
        worksheet.right_to_left()

        # Auto column width
        for i, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, max_len)

        # Header format
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#000000',
            'font_color': '#FFFFFF',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })

        # Body formats
        body_format = workbook.add_format({
            'border': 1,
            'border_color': '#FFFFFF',
            'bg_color': '#D9EAF7'
        })

        alt_body_format = workbook.add_format({
            'border': 1,
            'border_color': '#FFFFFF',
            'bg_color': '#F2F2F2'
        })

        # Apply header
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)

        # Apply striped rows
        for row_num in range(1, len(df) + 1):
            fmt = body_format if row_num % 2 else alt_body_format
            worksheet.set_row(row_num, None, fmt)

# --------------------
#  Save Form B102 Report Data To Folder
# ---------------------- 

@app.route("/save_formB102_report", methods=["POST"])
@login_required
def save_formB102_report():
    import os, json
    data = request.json

    month = data["employer"]["reportMonth"]
    year = data["employer"]["reportYear"]

    # === יצירת תיקייה ראשית ===
    base_dir = os.path.join(app.root_path, "form_B102_report")
    os.makedirs(base_dir, exist_ok=True)

    # === יצירת תיקייה לפי שנה ===
    year_folder = os.path.join(base_dir, f"Form_B102_{year}")
    os.makedirs(year_folder, exist_ok=True)

    # === יצירת שמות קבצים ===
    filename_json = f"Form_B102_report_{month}_{year}.json"
    filename_xml = f"Form_B102_report_{month}_{year}.xml"

    json_path = os.path.join(year_folder, filename_json)
    xml_path = os.path.join(year_folder, filename_xml)

    # === שמירת JSON ===
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # === שמירת XML ===
    xml_content = data["xml"]
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(xml_content)

    return jsonify({
        "success": True,
        "json_file": filename_json,
        "xml_file": filename_xml,
        "folder": year_folder
    })

# --------------------
#   Convert Fields Name From App To Tax Office Name Report Form B102 Form Data
# ----------------------

# mapping between form field names (HTML) and model attributes (DB)
FIELD_MAP_B102 = {

    # ----- Employer info -----
    "companyName": ["company_name"],
    "taxFileNumber": ["taxFileNumber"],
    "reportMonth": ["selected_month"],
    "reportYear": ["selected_year"],

    # ----- Employee totals -----
    "NumEmployees": ["employee_count"],

    "regular_salary": ["regular_salary_hidden"],
    "reduced_salary": ["reduced_salary_hidden"],


    # שכר מעל תקרה לעובד (רק אם חישבת)
    "employeeAboveMaxSalary": ["employee_above_max"],

    # שכר מופחת למעסיק = שכר מופחת לעובד
    "employerReducedSalary": ["reduced_salary_hidden"],

    # שכר מעל תקרה למעסיק = כמו עובד
    "employerAboveMaxSalary": ["employee_above_max"],

    # ספירת עובדים רגילים / מופחתים
    "regular_count": ["regular_count_hidden"],
    "reducedEmployeeCount": ["reduced_count_hidden"],   

    # סה״כ שכר
    "total_salary": ["total_salary_hidden"],

    # ----- Original totals -----
    "totalGrossSalary": ["total_gross"],
    "totalIncomeTax": ["total_income_tax"],
    "totalNationalInsurance": ["total_ni_employee"],
    "totalHealthInsurance": ["total_health"],
    "totalEmpPension": ["emp_pension"],
    "totalSelfPension": ["self_pension"],
    "totalPensionDeduction": ["final_emp_pension_combined"],
    "totalProvidentDeduction": ["total_study_fund_deductions"],

    # ----- Employer contributions -----
    "totalPensionVal": ["pension_val"],
    "totalCompVal": ["comp_val"],
    "totalDisabilityVal": ["disability_val"],
    "employerPension": ["total_employer_pension_combined"],
    "totalStudyFundVal": ["study_fund_val"],

    # ----- Summary -----
    "totalEmpDeductions": ["final_emp_deductions_total"],
    "totalContributions": ["total_employer_contributions"],
    "finalTotalsPaid": ["finalTotalsPaid"],
    "finalTotalIncomeTax": ["final_totals_income_tax"],

    #  טור 4 שורה 8 = שורה 7
    "reducedEmployeeCount_total": ["finalTotalsPaid"],
}


# --------------------
# Send Form B102 To Tax Office Requst Data
# ----------------------

@app.route('/send_B102_to_tax', methods=['POST'])
@login_required
def send_B102_to_tax():
    if not session.get("owner_access"):
        flash("⛔ רק בעלים יכול לשדר לרשות המיסים.", "danger")
        return redirect(url_for('form_B102'))

    # קובץ ה‑XML שנוצר קודם
    xml_path = session.get("generated_xml_path")

    if not xml_path or not os.path.exists(xml_path):
        flash("קובץ XML לא נמצא — צור אותו מחדש.", "danger")
        return redirect(url_for('form_B102'))

    # טוען את ה‑XML
    with open(xml_path, "rb") as f:
        xml_data = f.read()

    #  URL דמיוני — אתה תחליף לכתובת האמיתית
    TAX_URL = "https://tax.gov.il/api/B102/upload"

    #  תעודה דיגיטלית — אתה תחליף לשם הקובץ שלך
    CERT_FILE = "certs/company_cert.pfx"
    CERT_PASS = "12345678"  # תחליף לסיסמה שלך

    try:
        response = requests.post(
            TAX_URL,
            data=xml_data,
            cert=(CERT_FILE, CERT_PASS),
            headers={"Content-Type": "text/xml"},
            timeout=30
        )

        # שומר את התשובה בתיקייה
        log_path = xml_path.replace(".xml", "_response.xml")
        with open(log_path, "wb") as f:
            f.write(response.content)

        flash("השידור בוצע. התקבלה תשובה מרשות המיסים.", "info")
        return redirect(url_for('form_B102'))

    except Exception as e:
        flash(f"שגיאה בשידור: {str(e)}", "danger")
        return redirect(url_for('form_B102'))


# --------------------
# Clear Form B102 Data
# ----------------------

@app.route('/clear_formB102', methods=['POST'])
@login_required
def clear_formB102():
    session['clear_B102'] = True
    return redirect(url_for('form_B102'))



# --------------------
#  Form H102 Form Data
# ----------------------

@app.route('/form_H102', methods=['GET', 'POST'])
@login_required
def form_H102():
    employees = EmployeeData.query.all()
    company_data = load_company_data()

    # ----- בסיס זמן -----
    now = datetime.now()
    months = range(1, 13)
    years = range(now.year - 2, now.year + 2)

    #  POST — שמירת נתונים
    if request.method == 'POST':

        new_employee_id = request.form.get('employee_id')
        old_employee_id = session.get('employee_id')

        #  אם המשתמש החליף עובד בתוך הטופס → ננקה לפני טעינה מחדש
        if new_employee_id != old_employee_id:
            session['form_data'] = {}
            session['employee_id'] = new_employee_id
            return redirect(url_for('form_H102'))

        #  שמירת חודש/שנה
        if request.form.get('reportMonth'):
            session['selected_month'] = int(request.form.get('reportMonth'))
        if request.form.get('reportYear'):
            session['selected_year'] = int(request.form.get('reportYear'))

        #  שמירת נתוני עובד
        employee = EmployeeData.query.get(new_employee_id)
        if employee:
            for form_field, model_attrs in FIELD_MAP_H102.items():
                if form_field in request.form:
                    value = request.form.get(form_field)
                    for attr in model_attrs:
                        if hasattr(employee, attr):
                            setattr(employee, attr, value)
            db.session.commit()

        #  שמירת נתוני הטופס ב-session
        session['form_data'] = request.form.to_dict()

        flash('נתוני טופס H102 עודכנו בהצלחה!', 'success')
        return redirect(url_for('form_H102'))

    #  GET — קריאת פרמטרים מה-URL או מה-session
    selected_employee_id = request.args.get('employee_id') or session.get('employee_id', '')
    selected_month = request.args.get('month')
    selected_year = request.args.get('year')

    selected_month = int(selected_month) if selected_month else int(session.get('selected_month', now.month))
    selected_year = int(selected_year) if selected_year else int(session.get('selected_year', now.year))

    #  ניקוי טופס H102 לפי בקשה מפורשת
    if session.pop('clear_H102', None):
        return render_template(
            'form_H102.html',
            form_data={},
            employees=employees,
            employee_data={},
            selected_employee_id='',
            time=time,
            employeeMonth='',
            employeeYear='',
            months=months,
            years=years
        )

    #  זיהוי שינוי עובד / חודש / שנה
    previous_employee_id = session.get('employee_id')
    previous_month = session.get('selected_month')
    previous_year = session.get('selected_year')

    employee_changed = previous_employee_id and selected_employee_id and previous_employee_id != selected_employee_id
    month_changed = previous_month and selected_month and int(previous_month) != int(selected_month)
    year_changed = previous_year and selected_year and int(previous_year) != int(selected_year)

    #  אם משהו השתנה → ננקה רק את נתוני הטופס
    if employee_changed or month_changed or year_changed:
        session['form_data'] = {}

    #  עדכון ה-session לערכים החדשים
    session['employee_id'] = selected_employee_id
    session['selected_month'] = selected_month
    session['selected_year'] = selected_year

    #  אם אין form_data — אל תחשב totals, תחזיר טופס ריק
    if not session.get('form_data'):
        return render_template(
            'form_H102.html',
            form_data={},
            employees=employees,
            employee_data={},
            selected_employee_id=session.get('employee_id', ''),
            time=time,
            employeeMonth=selected_month,
            employeeYear=selected_year,
            months=months,
            years=years
        )

    #  AJAX GET — שליפת נתוני עובד
    if request.method == 'GET' and request.args.get('action') == 'get_employee_data':
        employee_id = request.args.get('employee_id')
        m = request.args.get('month') or selected_month
        y = request.args.get('year') or selected_year
        details = get_employee_details(employee_id, m, y)
        return jsonify({'success': bool(details), **(details or {})})

    #  חישוב totals
    form_data = session.get('form_data', {})
    all_hours = load_hours(selected_year) or {}

    employee_count = 0
    total_gross = 0.0
    total_income_tax = 0.0
    total_ni_employee = 0.0
    total_health = 0.0
    total_study_fund_deductions = 0.0

    emp_pension = 0.0
    self_pension = 0.0

    pension_val = 0.0
    comp_val = 0.0
    disability_val = 0.0
    study_fund_val = 0.0

    regular_salary = 0.0
    reduced_salary = 0.0
    regular_count = 0
    reduced_count = 0

    month_key = f"{selected_year}-{str(selected_month).zfill(2)}"

    # Clean Number helper
    def cn(val):
        try:
            return float(str(val).replace("₪", "").replace(",", "").strip())
        except:
            return 0.0

    for emp_id, emp_months in all_hours.items():
        if month_key in emp_months:
            employee_count += 1

            tax_data = emp_months[month_key].get("hours_table", {}).get("tax", {})

            gross_taxable = cn(tax_data.get("gross_taxable", 0))
            dob = tax_data.get("date_of_birth") or None

            #  חישוב שכר רגיל / מופחת לפי גיל
            if dob:
                try:
                    birth = datetime.strptime(dob, "%Y-%m-%d")
                    today = datetime.today()
                    age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
                except:
                    age = 0
            else:
                age = 0

            if age < 18 or age >= 67:
                reduced_salary += gross_taxable
                reduced_count += 1
            else:
                regular_salary += gross_taxable
                regular_count += 1

            total_gross += gross_taxable
            total_income_tax += cn(tax_data.get("income_tax", 0))
            total_ni_employee += cn(tax_data.get("national_insurance_deductions", 0))
            total_health += cn(tax_data.get("health_insurance_deductions", 0))
            total_study_fund_deductions += cn(tax_data.get("study_fund_deductions", 0))

            emp_pension += cn(tax_data.get("employee_pension_fund", 0))
            self_pension += cn(tax_data.get("self_employed_pension_fund", 0))

            pension_val += cn(tax_data.get("pension_fund", 0))
            comp_val += cn(tax_data.get("compensation", 0))
            disability_val += cn(tax_data.get("disability", 0))
            study_fund_val += cn(tax_data.get("study_fund", 0))

    final_emp_pension_combined = emp_pension + self_pension

    final_emp_deductions_total = (
        total_ni_employee +
        total_health +
        final_emp_pension_combined +
        total_study_fund_deductions
    )

    total_employer_pension_combined = (
        pension_val +
        comp_val +
        disability_val +
        study_fund_val
    )

    final_totals_paid = (
        final_emp_deductions_total +
        total_employer_pension_combined
    )

    final_totals_income_tax = total_income_tax

    # ====== התאמה לטופס H102 ======
    # נניח שכל המס שנוכה הוא "מס ממשכורת בתחום אילת" (א),
    # בלי פירוק לבעלי שליטה / מחוץ לאילת (אפשר לעדכן לוגיקה בהמשך אם תרצה).

    eilat_regular_tax = total_income_tax
    eilat_benefit_20 = eilat_regular_tax * 0.20
    eilat_total_tax_after_benefit = eilat_regular_tax - eilat_benefit_20

    controlling_salary = 0.0
    controlling_tax = 0.0
    outside_eilat_salary = 0.0
    outside_eilat_tax = 0.0

    total_tax_all = (
        eilat_total_tax_after_benefit +
        controlling_tax +
        outside_eilat_tax
    )

    form_data.update({
        'NumEmployees': employee_count,
        'regular_salary_hidden': round_form_number(regular_salary),
        'reduced_salary_hidden': round_form_number(reduced_salary),
        'regular_count_hidden': regular_count,
        'reduced_count_hidden': reduced_count,
        'total_salary_hidden': round_form_number(regular_salary + reduced_salary),
         
        'totalGrossSalary': round_form_number(total_gross),
        'totalIncomeTax': round_form_number(total_income_tax),
        'totalNationalInsurance': round_form_number(total_ni_employee),
        'totalHealthInsurance': round_form_number(total_health),
        'totalProvidentDeduction': round_form_number(total_study_fund_deductions),

        'totalEmpPension': round_form_number(emp_pension),
        'totalSelfPension': round_form_number(self_pension),
        'totalPensionDeduction':round_form_number(final_emp_pension_combined),

        'totalPensionVal': round_form_number(pension_val),
        'totalCompVal': round_form_number(comp_val),
        'totalDisabilityVal': round_form_number(disability_val),
        'totalStudyFundVal': round_form_number(study_fund_val),
        'employerPension': round_form_number(total_employer_pension_combined),

        'totalEmpDeductions': round_form_number(final_emp_deductions_total),
        'finalTotalsPaid': round_form_number(final_totals_paid),
        'finalTotalIncomeTax': round_form_number(final_totals_income_tax),

        # ----- שדות H102 עצמם -----
        'eilat_regular_tax': round_form_number(eilat_regular_tax),
        'eilat_benefit_20': round_form_number(eilat_benefit_20),
        'eilat_total_tax_after_benefit': round_form_number(eilat_total_tax_after_benefit),

        'controlling_salary': round_form_number(controlling_salary),
        'controlling_tax': round_form_number(controlling_tax),

        'outside_eilat_salary': round_form_number(outside_eilat_salary),
        'outside_eilat_tax': round_form_number(outside_eilat_tax),

        'total_tax_all': round_form_number(total_tax_all),

        'reportMonth': selected_month,
        'reportYear': selected_year
    })

    form_data.setdefault("companyName", company_data.get("name", ""))
    form_data.setdefault("taxFileNumber", company_data.get("תיק ניכויים", ""))
    form_data.setdefault("companyAddress", company_data.get("address", ""))

    # Extract city from companyAddress
    address = form_data.get("companyAddress", "")
    parts = address.split(',')
    company_city = parts[1].strip() if len(parts) > 1 else ""

    session["form_data"] = form_data

    return render_template(
        'form_H102.html',
        form_data=form_data,
        company_city=company_city,
        employees=employees,
        employee_data=session.get('employee_data', {}),
        selected_employee_id=session.get('employee_id', ''),
        time=time,
        selected_month=selected_month,
        selected_year=selected_year,
        months=months,
        years=years
    )


@app.route('/submitH102', methods=['POST'])
def submit_form_H102():
    data = request.form.to_dict()
    return jsonify(data)


# --------------------
# Save Form H102 Data 
# ---------------------- 

@app.route('/save_form_H102', methods=['POST'])
@login_required
def save_form_H102():
    try:
        data = request.get_json() or {}

        # 1) קריאת פרמטרים בסיסיים
        employee_id = str(data.get("employee_id", "")).strip()
        employee_name = data.get("employee_name", "").strip()
        month = str(data.get("reportMonth", "")).zfill(2)
        year = str(data.get("reportYear", ""))

        if not employee_id or not month or not year:
            return jsonify(success=False, message="חסרים פרמטרים לשמירה"), 400

        month_key = f"{year}-{month}"

        # === 2) יצירת תיקייה ראשית form_H102 ===
        base_dir = os.path.join(app.root_path, "form_H102")
        os.makedirs(base_dir, exist_ok=True)

        # === 3) יצירת תיקייה לפי שנה ===
        year_folder = os.path.join(base_dir, f"H102_{year}")
        os.makedirs(year_folder, exist_ok=True)

        # === 4) שמירה ל־JSON לפי חודש ===
        json_path = os.path.join(year_folder, f"H102_{month}_{year}.json")

        # טוען קובץ קיים אם יש
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                month_data = json.load(f)
        else:
            month_data = {}

        # עדכון נתוני העובד
        month_data[employee_id] = {
            "employee_name": employee_name,
            "form_data": data
        }

        # כתיבה לקובץ JSON
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(month_data, f, ensure_ascii=False, indent=4)

        # === 5) בניית CSV ===
        csv_path = os.path.join(year_folder, f"H102_{month}_{year}.csv")

        fieldnames = list(data.keys())

        with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(data)

        # === 6) יצירת XLSX ===
        xlsx_path = os.path.join(year_folder, f"H102_{month}_{year}.xlsx")

        df = pd.DataFrame([data])
        save_H102_excel(csv_path, xlsx_path)

        # === 7) עדכון session ===
        session["form_H102"] = data

        return jsonify(success=True, message="טופס H102 נשמר בהצלחה!")

    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

# ----------------------
#  Save To Csv And Xlsx All Data On Folder Form H102
# ----------------------

def save_H102_excel(csv_path, xlsx_path):
    if not os.path.exists(csv_path):
        return

    df = pd.read_csv(csv_path, encoding='utf-8-sig')

    with pd.ExcelWriter(xlsx_path, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='FormH102')

        workbook  = writer.book
        worksheet = writer.sheets['FormH102']

        # Freeze header
        worksheet.freeze_panes(1, 0)

        # RTL
        worksheet.right_to_left()

        # Auto column width
        for i, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, max_len)

        # Header format
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#000000',
            'font_color': '#FFFFFF',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })

        # Body formats
        body_format = workbook.add_format({
            'border': 1,
            'border_color': '#FFFFFF',
            'bg_color': '#D9EAF7'
        })

        alt_body_format = workbook.add_format({
            'border': 1,
            'border_color': '#FFFFFF',
            'bg_color': '#F2F2F2'
        })

        # Apply header
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)

        # Apply striped rows
        for row_num in range(1, len(df) + 1):
            fmt = body_format if row_num % 2 else alt_body_format
            worksheet.set_row(row_num, None, fmt)

# --------------------
#  Save Form H102 Report Data To Folder
# ---------------------- 

@app.route("/save_formH102_report", methods=["POST"])
@login_required
def save_formH102_report():
    import os, json
    data = request.json

    month = data["employer"]["reportMonth"]
    year = data["employer"]["reportYear"]

    # === יצירת תיקייה ראשית ===
    base_dir = os.path.join(app.root_path, "form_H102_report")
    os.makedirs(base_dir, exist_ok=True)

    # === יצירת תיקייה לפי שנה ===
    year_folder = os.path.join(base_dir, f"Form_H102_{year}")
    os.makedirs(year_folder, exist_ok=True)

    # === יצירת שמות קבצים ===
    filename_json = f"Form_H102_report_{month}_{year}.json"
    filename_xml = f"Form_H102_report_{month}_{year}.xml"

    json_path = os.path.join(year_folder, filename_json)
    xml_path = os.path.join(year_folder, filename_xml)

    # === שמירת JSON ===
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # === שמירת XML ===
    xml_content = data["xml"]
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(xml_content)

    return jsonify({
        "success": True,
        "json_file": filename_json,
        "xml_file": filename_xml,
        "folder": year_folder
    })

# --------------------
#   Convert Fields Name From App To Tax Office Name Report Form H102 Form Data
# ----------------------

# mapping between form field names (HTML) and model attributes (DB)
FIELD_MAP_H102 = {

    #   Employer Information
    "companyName": ["companyName"],
    "taxFileNumber": ["taxFileNumber"],
    "reportMonth": ["reportMonth"],
    "reportYear": ["reportYear"],

    "NumEmployees": ["employee_count"],

    "regular_salary": ["regular_salary_hidden"],
    "reduced_salary": ["reduced_salary_hidden"],

    # שכר מעל תקרה לעובד (רק אם חישבת)
    "employeeAboveMaxSalary": ["employee_above_max"],

    # שכר מופחת למעסיק = שכר מופחת לעובד
    "employerReducedSalary": ["reduced_salary_hidden"],

    # שכר מעל תקרה למעסיק = כמו עובד
    "employerAboveMaxSalary": ["employee_above_max"],

    # ספירת עובדים רגילים / מופחתים
    "regular_count": ["regular_count_hidden"],
    "reducedEmployeeCount": ["reduced_count_hidden"],   

    # סה״כ שכר
    "total_salary": ["total_salary_hidden"],

    # ----- Original totals -----
    "totalGrossSalary": ["total_gross"],
    "totalIncomeTax": ["total_income_tax"],
    "totalNationalInsurance": ["total_ni_employee"],
    "totalHealthInsurance": ["total_health"],
    "totalEmpPension": ["emp_pension"],
    "totalSelfPension": ["self_pension"],
    "totalPensionDeduction": ["final_emp_pension_combined"],
    "totalProvidentDeduction": ["total_study_fund_deductions"],

    # ----- Employer contributions -----
    "totalPensionVal": ["pension_val"],
    "totalCompVal": ["comp_val"],
    "totalDisabilityVal": ["disability_val"],
    "employerPension": ["total_employer_pension_combined"],
    "totalStudyFundVal": ["study_fund_val"],

    # ----- Summary -----
    "totalEmpDeductions": ["final_emp_deductions_total"],
    "totalContributions": ["total_employer_contributions"],
    "finalTotalsPaid": ["finalTotalsPaid"],
    "finalTotalIncomeTax": ["final_totals_income_tax"],

    #  טור 4 שורה 8 = שורה 7
    "reducedEmployeeCount_total": ["finalTotalsPaid"],

    #   Column A (א)
    "regularSalary": ["regular_salary_hidden"],
    "eilatRegularTax": ["eilat_regular_tax"],
    "eilatBenefit20": ["eilat_benefit_20"],
    "eilatTotalTaxAfterBenefit": ["eilat_total_tax_after_benefit"],

    #   Column B (ב)
    "controllingSalary": ["controlling_salary"],
    "controllingTax": ["controlling_tax"],

    #   Column C (ג)
    "outsideEilatSalary": ["outside_eilat_salary"],
    "outsideEilatTax": ["outside_eilat_tax"],
    "totalTaxAll": ["total_tax_all"],
}


# --------------------
# Send Form H102 To Tax Office Requst Data
# ----------------------

@app.route('/send_H102_to_tax', methods=['POST'])
@login_required
def send_H102_to_tax():
    if not session.get("owner_access"):
        flash("⛔ רק בעלים יכול לשדר לרשות המיסים.", "danger")
        return redirect(url_for('form_H102'))

    # קובץ ה‑XML שנוצר קודם
    xml_path = session.get("generated_xml_path")

    if not xml_path or not os.path.exists(xml_path):
        flash("קובץ XML לא נמצא — צור אותו מחדש.", "danger")
        return redirect(url_for('form_H102'))

    # טוען את ה‑XML
    with open(xml_path, "rb") as f:
        xml_data = f.read()

    #  URL דמיוני — אתה תחליף לכתובת האמיתית
    TAX_URL = "https://tax.gov.il/api/H102/upload"

    #  תעודה דיגיטלית — אתה תחליף לשם הקובץ שלך
    CERT_FILE = "certs/company_cert.pfx"
    CERT_PASS = "12345678"  # תחליף לסיסמה שלך

    try:
        response = requests.post(
            TAX_URL,
            data=xml_data,
            cert=(CERT_FILE, CERT_PASS),
            headers={"Content-Type": "text/xml"},
            timeout=30
        )

        # שומר את התשובה בתיקייה
        log_path = xml_path.replace(".xml", "_response.xml")
        with open(log_path, "wb") as f:
            f.write(response.content)

        flash("השידור בוצע. התקבלה תשובה מרשות המיסים.", "info")
        return redirect(url_for('form_H102'))

    except Exception as e:
        flash(f"שגיאה בשידור: {str(e)}", "danger")
        return redirect(url_for('form_H102'))


# --------------------
# Clear Form H102 Data
# ----------------------

@app.route('/clear_formH102', methods=['POST'])
@login_required
def clear_formH102():
    session['clear_H102'] = True
    return redirect(url_for('form_H102'))



# --------------------
#  Form 106 Compute Count Worked Months 
# ----------------------

def count_work_months(all_hours, employee_id, year):
    count = 0
    emp_data = all_hours.get(str(employee_id), {})

    for mk in emp_data.keys():
        if mk == "employee_name":
            continue
        if mk.startswith(str(year)):
            count += 1

    return count

# --------------------
#  Form 106 Form Data
# ----------------------

@app.route('/form_106', methods=['GET', 'POST'])
@login_required
def form_106():
    employees = EmployeeData.query.all()
    company_data = load_company_data()

    # YEAR ONLY
    selected_year = session.get('selected_year', datetime.now().year)
    years = range(datetime.now().year - 2, datetime.now().year + 2)

    # AJAX GET (load employee data dynamically)
    if request.method == 'GET' and request.args.get('action') == 'get_employee_data':
        employee_id = request.args.get('employee_id')
        details = get_employee_details(employee_id, None, request.args.get('year'))
        return jsonify({'success': bool(details), **(details or {})})

    # POST — SAVE FORM 106
    if request.method == 'POST':

        # Sync selected year only
        if request.form.get('reportYear'):
            session['selected_year'] = request.form.get('reportYear')

        employee_id = request.form.get('employee_id')
        employee = EmployeeData.query.get(employee_id)

        if not employee:
            flash('שגיאה: העובד לא נמצא.', 'error')
            return redirect(url_for('form_106'))

        # Basic employee fields
        employee.employee_name = request.form.get('employee_name')
        employee.id_number = request.form.get('id_number')
        employee.address = request.form.get('address')
        employee.city = request.form.get('city')
        employee.postal_code = request.form.get('postal_code')

        # FIELD_MAP updates
        for form_field, model_attrs in FIELD_MAP_106.items():
            if form_field in request.form:
                value = request.form.get(form_field)
                for attr in model_attrs:
                    if hasattr(employee, attr):
                        setattr(employee, attr, value)

        db.session.commit()

        # Save form data for re-render
        session['form_data'] = request.form.to_dict()

        flash('נתוני טופס 106 עודכנו בהצלחה!', 'success')
        return redirect(url_for('form_106', employee_id=employee_id))

    # --- GET Part ---
    employee_id = request.args.get('employee_id') or session.get('employee_id')

    form_data = session.get('form_data', {})
    all_hours = load_hours(selected_year) or {}

    # Initialize summary variables
    final_yearly_gross = 0.0
    final_yearly_tax = 0.0
    final_pension_combined = 0.0
    final_deductions_total = 0.0
    months_worked = 0
    final_net_for_tax = 0.0  

    # Clean Number helper
    def cn(val):
        try:
            return float(str(val).replace("₪", "").replace(",", "").strip())
        except:
            return 0.0

    # YEARLY CALCULATION ONLY
    if employee_id and str(employee_id) in all_hours:
        emp_records = all_hours.get(str(employee_id), {})

        # Count months worked
        months_worked = count_work_months(all_hours, employee_id, selected_year)

        # Find any month of the selected year (yearly values identical)
        for month_key, month_data in emp_records.items():
            if month_key.startswith(str(selected_year)):
                tax_data = month_data.get("hours_table", {}).get("tax", {})

                final_yearly_gross = cn(tax_data.get("gross_taxable_yearly", 0))
                final_yearly_tax = cn(tax_data.get("income_tax_yearly", 0))

                emp_pension = cn(tax_data.get("employee_pension_fund_yearly", 0))
                self_pension = cn(tax_data.get("self_employed_pension_fund_yearly", 0))
                final_pension_combined = emp_pension + self_pension

                final_deductions_total = (
                    final_yearly_tax +
                    cn(tax_data.get("national_insurance_deductions_yearly", 0)) +
                    cn(tax_data.get("health_insurance_deductions_yearly", 0)) +
                    final_pension_combined +
                    cn(tax_data.get("study_fund_deductions_yearly", 0))
                )

                final_net_for_tax = final_yearly_gross - final_deductions_total
                break

    # Inject into form_data
    form_data.update({
        'totalIncome': f"{final_yearly_gross:,.2f}",
        'taxableIncome': f"{final_yearly_tax:,.2f}",
        'pensionDeduction': f"{final_pension_combined:,.2f}", 
        'totalDeductions': f"{final_deductions_total:,.2f}",
        'netSalary': f"{final_net_for_tax:,.2f}",  
        'monthsWorked': f"{months_worked}",      
        'reportYear': selected_year,
        'employee_id': employee_id
    })

    # Inject company JSON
    form_data.setdefault("companyName", company_data.get("name", ""))
    form_data.setdefault("taxFileNumber", company_data.get("תיק ניכויים", ""))
    form_data.setdefault("companyAddress", company_data.get("address", ""))
    form_data.setdefault("companyPhone", company_data.get("phone", ""))

    session["form_data"] = form_data

    return render_template(
        'form_106.html',
        form_data=form_data,
        employees=employees,
        employee_data=session.get('employee_data', {}),
        selected_employee_id=employee_id,
        time=time,
        employeeYear=selected_year,
        years=years
    )


@app.route('/submit106', methods=['POST'])
def submit_form_106():
    data = request.form.to_dict()
    return jsonify(data)


# --------------------
#   Convert Fields Name From App To Tax Office Name Report Form 106 Form Data
# ----------------------

# mapping between form field names (HTML) and model attributes (DB)
FIELD_MAP_106 = {
    # ----- Employer Details -----
    "companyName": ["companyName"],
    "taxFileNumber": ["tax_file_number"],
    "companyAddress": ["address", "city", "postal_code", "companyAddress"],
    "reportYear": ["year"],

    # ----- Employee Details -----
    "fullName": ["employee_name", "full_name"],
    "idNumber": ["id_number", "employee_id"],
    "employeeAddress": ["address", "city", "postal_code", "employee_address"],
    "monthsWorked": ["months_worked", "total_work_days"],

    # ----- Income -----
    "grossSalary": ["gross_salary", "basic_salary", "gross_taxable_yearly"],
    "bonuses": ["thirteenth_salary", "additional_payments", "bonus"],
    "benefits": ["mobile_value", "clothing_value", "cars_value", "lunch_value", "benefits"],
    "severance": ["compensation_yearly", "severance"],
    "pensionDeposits": [
        "pension_fund_yearly",
        "employee_pension_fund_yearly",
        "self_employed_pension_fund_yearly",
        "pensionDeposits"
    ],
    "providentFund": ["study_fund_yearly", "providentFund"],

    # ----- Deductions -----
    "incomeTax": ["income_tax_yearly", "income_tax"],
    "nationalInsurance": ["national_insurance_deductions_yearly", "national_insurance"],
    "healthInsurance": ["health_insurance_deductions_yearly", "health_insurance"],
    "pensionDeduction": ["pensionDeduction"], 
    "providentDeduction": ["study_fund_deductions_yearly", "providentDeduction"],

    # ----- Summary -----
    "totalIncome": ["gross_taxable_yearly", "totalIncome"],
    "taxableIncome": ["gross_taxable_yearly", "taxableIncome"],
    "totalDeductions": ["totalDeductions"],
    "netSalary": ["netSalary"]
}



# --------------------
#  Form 161 Form Data
# ----------------------

@app.route('/form_161', methods=['GET', 'POST'])
@login_required
def form_161():
    employees = EmployeeData.query.all()
    company_data = load_company_data()

    # Load saved form data
    form_data = session.get('form_161_data', {})

    # AJAX GET — Load employee details
    if request.method == 'GET' and request.args.get('action') == 'get_employee_data':
        employee_id = request.args.get('employee_id')
        details = get_employee_details(employee_id)
        return jsonify({'success': bool(details), **(details or {})})

    # POST — Save form data
    if request.method == 'POST':
        employee_id = request.form.get('employee_id')
        employee = EmployeeData.query.get(employee_id)

        if employee:
            for form_field, model_attrs in FIELD_MAP_161.items():
                if form_field in request.form:
                    value = request.form.get(form_field)
                    for attr in model_attrs:
                        if hasattr(employee, attr):
                            setattr(employee, attr, value)

            db.session.commit()

        # Save form data to session
        session['form_161_data'] = request.form.to_dict()

        flash('טופס 161 נשמר בהצלחה!', 'success')
        return redirect(url_for('form_161'))

    # Inject company data
    form_data.setdefault("companyName", company_data.get("name", ""))
    form_data.setdefault("employer_id_number", company_data.get("תיק ניכויים", ""))
    form_data.setdefault("companyAddress", company_data.get("address", ""))

    session["form_data"] = form_data

    return render_template(
        'form_161.html',
        time=time,
        form_data=form_data,
        employees=employees,
        selected_employee_id=session.get('employee_id', '')
    )


@app.route('/submit161', methods=['POST'])
def submit_form_161():
    data = request.form.to_dict()
    return jsonify(data)


# --------------------
#   Convert Fields Name From App To Tax Office Name Report Form 161 Form Data
# ----------------------

FIELD_MAP_161 = {
    'employee_first_name': ['first_name'],
    'employee_last_name': ['last_name'],
    'employee_id_number': ['id_number'],
    'employee_address': ['address'],
    'employee_birth_date': ['birth_date'],

    'employer_name': ['employer_name'],
    'employer_id_number': ['employer_id'],
    'companyAddress': ['companyAddress'],
    'companyPhone': ['companyPhone'],

    'employment_start_date': ['start_date'],
    'employment_end_date': ['end_date'],
    'termination_reason': ['termination_reason'],

    'last_salary': ['last_salary'],
    'seniority_years': ['seniority_years'],
    'severance_paid': ['severance_paid'],
    'severance_in_funds': ['severance_in_funds'],
    'severance_exempt': ['severance_exempt'],
    'severance_taxable': ['severance_taxable'],

    'fund_name': ['fund_name'],
    'fund_number': ['fund_number'],
    'fund_balance': ['fund_balance'],
    'fund_released': ['fund_released'],

    'tax_route': ['tax_route'],
    'form_date': ['form_date']
}



# ----------------------
#   Build All Employee City Car Form
# ----------------------

#  Load Excel files City Car Form
df1 = pd.read_excel('Car.xlsm', sheet_name='Car', engine='openpyxl')
df2 = pd.read_excel('City.xlsm', sheet_name='City', engine='openpyxl')

# Separate DataFrames
df_car = df1.copy()
df_city = df2.copy()

# ----------------------
# Contact Employee_id: Contact Form Submission
# ----------------------
@app.route('/contact_form', methods=['GET', 'POST'])
@login_required
def contact_form():
    # Initialize session variables
    session.setdefault('car_data', None)
    session.setdefault('city_data', None)
    session.setdefault('car_form_fields', {'car_year': '', 'car_model': '', 'car_type': ''})
    session.setdefault('city_form_fields', {'city_name': ''})
    session.setdefault('employee_data', {})

    if request.method == 'POST':
        form_type = request.form.get('form_type')

        # 1. City Form Submission
        if form_type == 'city_form':
            city_name = request.form.get('city_name', '')
            session['city_form_fields']['city_name'] = city_name

            if city_name:
                filtered_df = df_city[df_city['שם יישוב'] == city_name]
                if not filtered_df.empty:
                    city_sign = str(filtered_df.iloc[0]['סמל היישוב'])
                    city_top_tax = int(filtered_df.iloc[0]['סכום זיכוי'])
                    city_value = float(filtered_df.iloc[0]['שיעור 2024'])
                    city_value_percentage = f"{city_value * 100:.2f}%"
                    monthly_city_top_tax = city_top_tax / 12
                    formatted_monthly_city_top_tax = format_currency(monthly_city_top_tax)

                    session['city_data'] = {
                        'שם יישוב': city_name,
                        'שיעור 2024': city_value_percentage,
                        'city_value_percentage': city_value,
                        'סמל היישוב': city_sign,
                        'סכום זיכוי': format_currency(city_top_tax),
                        'סכום זיכוי חודשי': formatted_monthly_city_top_tax,
                        'monthly_city_tax_tops': monthly_city_top_tax
                    }

        # Clear City Form
        elif form_type == 'clear_city_form':
            session['city_data'] = None
            session['city_form_fields'] = {'city_name': ''}

        # 2. Car Form Submission
        elif form_type == 'car_form':
            car_year = request.form.get('car_year', '')
            car_model = request.form.get('car_model', '')
            car_type = request.form.get('car_type', '')
            session['car_form_fields'] = {
                'car_year': car_year,
                'car_model': car_model,
                'car_type': car_type
            }

            if all(session['car_form_fields'].values()):
                try:
                    filtered_df = df_car[
                        (df_car['שנת רישום'] == int(car_year)) &
                        (df_car['קוד תוצר'] == int(car_model)) &
                        (df_car['קוד דגם'] == int(car_type))
                    ]
                except (ValueError, TypeError):
                    filtered_df = pd.DataFrame()

                if not filtered_df.empty:
                    car_value_raw = filtered_df.iloc[0]['שווי שימוש']
                    car_value = float(car_value_raw)
                    formatted_car_value = format_currency(car_value)

                    session['car_data'] = {
                        'car_year': car_year,
                        'car_model': car_model,
                        'car_type': car_type,
                        'שווי שימוש': formatted_car_value
                    }

        # Clear Car Form
        elif form_type == 'clear_car':
            session['car_data'] = None
            session['car_form_fields'] = {'car_year': '', 'car_model': '', 'car_type': ''}

        # 3. Contact Form Submission
        elif form_type == 'contact_form':
            employee_name = request.form.get('employee_name', '').strip()
            id_number = request.form.get('id_number', '').strip()
            date_str = request.form.get('date')

            if not employee_name or not id_number or not date_str:
                flash("שם העובד, מספר זהות ותאריך הם שדות חובה", "error")
                return redirect(url_for('contact_form'))

            parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
            formatted_date = parsed_date.strftime('%d/%m/%Y')

            # 1. CREATE OR FIND USER ACCOUNT
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '').strip()

            user = User.query.filter_by(email=email).first()
            if not user:
                user = User(
                    email=email,
                    role='employee'
                )
                user.set_password(password)
                db.session.add(user)
                db.session.commit()

            # 2. BUILD EMPLOYEE DATA
            form_data = {
                'user_id': user.id,
                'employee_name': employee_name,
                'id_number': id_number,
                'date': formatted_date,
                'address': request.form.get('address', '').strip(),
                'city': request.form.get('city', '').strip(),
                'postal_code': request.form.get('postal_code', '').strip(),
                'phone': request.form.get('phone', '').strip(),
                'email': email,
                'start_date': request.form.get('start_date', '').strip(),
                'date_of_birth': request.form.get('date_of_birth', '').strip(),
                'bank_number': request.form.get('bank_number', '').strip(),
                'branch_number': request.form.get('branch_number', '').strip(),
                'account_number': request.form.get('account_number', '').strip(),
                'clothing_value': to_float(request.form.get('clothing_value')),
                'cars_value': to_float(request.form.get('cars_value')),
                'monthly_city_tax_tops': to_float(request.form.get('monthly_city_tax_tops')),
                'city_value_percentage': to_float(request.form.get('city_value_percentage')),
                'lunch_value': to_float(request.form.get('lunch_value')),
                'mobile_value': to_float(request.form.get('mobile_value')),
                'hourly_rate': to_float(request.form.get('hourly_rate')),
                'employee_number': request.form.get('employee_number', '').strip(),
                'thirteenth_salary': to_float(request.form.get('thirteenth_salary')),
                'message': request.form.get('message', '').strip(),
                'work_apartment': request.form.get('work_apartment', '').strip(),
                'work_percent': to_float(request.form.get('work_percent')),
                'marital_status': request.form.get('marital_status', '').strip(),
                'tax_credit_points': to_float(request.form.get('tax_credit_points')),
                'hospital': request.form.get('hospital', '').strip(),
                'social_number': request.form.get('social_number', '').strip(),
                'irs_status': request.form.get('irs_status', '').strip(),
                'contract_status': request.form.get('contract_status', '').strip(),
                'tax_point_child': to_float(request.form.get('tax_point_child')),
                'role': request.form.get('role', 'עובד').strip()
            }

            # בדיקה אם העובד כבר קיים לפי ת"ז
            employee = EmployeeData.query.filter_by(id_number=id_number).first()

            if employee:
                for key, value in form_data.items():
                    setattr(employee, key, value)
            else:
                employee = EmployeeData(**form_data)
                db.session.add(employee)

            db.session.commit()
            session['employee_data'] = form_data

            # שליחת מייל
            try:
                msg = Message(
                    subject="פרטי העובד שלך נשמרו בהצלחה",
                    sender=app.config['MAIL_USERNAME'],
                    recipients=[employee.email]
                )
                msg.html = render_template('email_template.html', employee=employee)
                mail.send(msg)
                flash("המייל נשלח בהצלחה!", "success")
            except Exception as e:
                db.session.rollback()
                flash(f"שגיאה בשליחת מייל: {str(e)}", "error")
                return redirect(url_for('contact_form'))

    # GET request or after POST – טעינת עובד לתצוגה
    employee = None

    employee_id = request.args.get('employee_id', type=int)
    if employee_id:
        employee = EmployeeData.query.get(employee_id)
    else:
        id_number = request.args.get('id_number', '').strip()
        if id_number:
            employee = EmployeeData.query.filter_by(id_number=id_number).first()

    return render_template(
        'contact_form.html',
        employee_data=session.get('employee_data', {}),
        employee=employee,
        formatted_monthly_city_top_tax=session['city_data']['סכום זיכוי חודשי'] if session.get('city_data') else '',
        formatted_car_value=session['car_data']['שווי שימוש'] if session.get('car_data') else '',
        cars_value=session.get('car_data'),
        car_form_fields=session.get('car_form_fields'),
        city_form_fields=session.get('city_form_fields'),
        car_data=session.get('car_data'),
        city_data=session.get('city_data'),
        contact_data=session.get('contact_data', {})
    )

# ----------------------
# Contact Data: Form Page
# ----------------------

@app.route('/contact_data')
@login_required
def contact_data():
    # שלב 1: שליפת כל העובדים מהמסד
    all_employees = EmployeeData.query.all()

    # שלב 2: עיבוד נתונים לכל עובד
    for emp in all_employees:
        # עיבוד תאריך — אם כבר בפורמט תקני, השאר אותו
        try:
            if isinstance(emp.date, str) and '/' in emp.date:
                emp.formatted_date = emp.date
            else:
                emp.formatted_date = datetime.strptime(str(emp.date), '%Y-%m-%d').strftime('%d/%m/%Y')
        except Exception:
            emp.formatted_date = emp.date  # במקרה של שגיאה, השאר את הערך המקורי

        # שלב 3: עיבוד שדות מספריים לפורמט עם פסיקים ונקודות עשרוניות
        try:
            emp.formatted_cars_value = '{:,.2f}'.format(float(emp.cars_value))
            emp.formatted_clothing_value = '{:,.2f}'.format(float(emp.clothing_value))
            emp.formatted_monthly_city_tax_tops = '{:,.2f}'.format(float(emp.monthly_city_tax_tops))
            emp.formatted_lunch_value = '{:,.2f}'.format(float(emp.lunch_value))
            emp.formatted_mobile_value = '{:,.2f}'.format(float(emp.mobile_value))
            emp.formatted_hourly_rate = '{:,.2f}'.format(float(emp.hourly_rate))
            emp.formatted_thirteenth_salary = '{:,.2f}'.format(float(emp.thirteenth_salary))
            emp.formatted_work_percent = '{:,.2f}'.format(float(emp.work_percent))
            emp.formatted_tax_credit_points = '{:,.2f}'.format(float(emp.tax_credit_points))
            emp.formatted_tax_point_child = '{:,.2f}'.format(float(emp.tax_point_child))
        except Exception:
            # במקרה של שגיאה בהמרה — שמור ערכים ריקים כדי למנוע קריסה
            emp.formatted_cars_value = ''
            emp.formatted_clothing_value = ''
            emp.formatted_monthly_city_tax_tops = ''
            emp.formatted_lunch_value = ''
            emp.formatted_mobile_value = ''
            emp.formatted_hourly_rate = ''
            emp.formatted_thirteenth_salary = ''
            emp.formatted_work_percent = ''
            emp.formatted_tax_credit_points = ''
            emp.formatted_tax_point_child = ''

    # שלב 4: שליחה לתבנית HTML
    return render_template('contact_data.html', employees=all_employees)

# ----------------------
# Contact Search Clear Employee: Form Page
# ----------------------

@app.route('/search_employee', methods=['GET', 'POST'])
@login_required
def search_employee():
    # Clear city data when searching employee
    session['city_data'] = None
    session['city_form_fields'] = {
        'city_name': '',
        'city_value': '',
        'city_sign': '',
        'city_top_tax': '',
        'monthly_city_top_tax': ''
    }

    session['car_data'] = None
    session['car_form_fields'] = {
        'car_year': '',
        'car_model': '',
        'car_type': '',
        'car_value': ''
    }

    search_name = request.form.get('search_name') if request.method == 'POST' else request.args.get('search_name')

    search_results = EmployeeData.query.filter(
        EmployeeData.employee_name.ilike(f'%{search_name}%')
    ).all() if search_name else []

    all_employees = EmployeeData.query.order_by(EmployeeData.employee_name).all()
    months = ['ינואר', 'פברואר', 'מרץ', 'אפריל', 'מאי', 'יוני', 'יולי',
              'אוגוסט', 'ספטמבר', 'אוקטובר', 'נובמבר', 'דצמבר']
    years = list(range(2020, 2031))
    days_data = get_days_in_month(2024, 1)

    employee = search_results[0] if search_results else None

    return render_template(
        'contact_form.html',
        months=months,
        years=years,
        days_data=days_data,
        employees=search_results,
        all_employees=all_employees,
        employee=employee,
        car_data=session['car_data'],
        city_data=session['city_data'],
        car_form_fields=session['car_form_fields'],
        city_form_fields=session['city_form_fields']
    )

@app.route('/clear_search_results_employee', methods=['POST'])
@login_required
def clear_search_results_employee():
    #  Step 1: Clear all session data
    session['employee_data'] = {}

    session['city_data'] = None
    session['city_form_fields'] = {
        'city_name': '',
        'city_value': '',
        'city_sign': '',
        'city_top_tax': '',
        'monthly_city_top_tax': ''
    }

    session['car_data'] = None
    session['car_form_fields'] = {
        'car_year': '',
        'car_model': '',
        'car_type': '',
        'car_value': ''
    }

    #  Step 2: Prepare static data for the form
    months = ['ינואר', 'פברואר', 'מרץ', 'אפריל', 'מאי', 'יוני', 'יולי',
              'אוגוסט', 'ספטמבר', 'אוקטובר', 'נובמבר', 'דצמבר']
    years = list(range(2020, 2031))
    days_data = get_days_in_month(2024, 1)

    #  Step 3: Load employee list
    all_employees = EmployeeData.query.order_by(EmployeeData.employee_name).all()
    employee = None

    #  Step 4: Flash message and render clean form
    flash('החיפוש נוקה בהצלחה!', 'info')

    return render_template(
        'contact_form.html',
        months=months,
        years=years,
        days_data=days_data,
        employees=[],  
        all_employees=all_employees,
        employee=employee,
        car_data=session['car_data'],
        city_data=session['city_data'],
        car_form_fields=session['car_form_fields'],
        city_form_fields=session['city_form_fields'],
        formatted_car_value='',
        formatted_monthly_city_top_tax=''
    )

# ----------------------
# Get Employee Details: Form Page
# ----------------------

@app.route('/get_employee_details/<int:employee_id>/<string:month>/<string:year>')
@login_required
def get_employee_details(employee_id, month, year):
    employee = EmployeeData.query.get(employee_id)

    if not employee:
        return jsonify({'error': 'עובד לא נמצא'}), 404

    try:
        # ----------------------
        # Helper Formatters
        # ----------------------

        def format_hours(value):
            return "" if value == 0 else str(int(value)) if value == int(value) else f"{value:.2f}"

        def format_currency(value):
            try:
                return f"{float(value):,.2f}"  # No ₪, just "12,345.67"
            except (ValueError, TypeError):
                return "0.00"

        def format_percentage(value):
            return f"{float(value):.2f}%" if value not in [None, ""] else "0.00%"

        def format_text(value):
            return value.strip() if isinstance(value, str) and value.strip() else "N/A"

        def format_date(value):
            try:
                date_obj = datetime.strptime(value, "%d/%m/%Y")
                return date_obj.strftime("%d/%m/%Y")
            except:
                return "N/A"

        def format_day_name(value):
            try:
                date_obj = datetime.strptime(value, "%d/%m/%Y")
                hebrew_days = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי', 'שבת']
                return hebrew_days[date_obj.weekday()]
            except:
                return "N/A"

        def safe_float(value):
            try:
                return float(value) if value.strip() != '' else None
            except:
                return None

        # ----------------------
        # Build Employee Data
        # ----------------------

        employee_data = {
            'employee_id': employee_id,
            'month_result': format_text(getattr(employee, 'month_result', "")),
            'employee_name': format_text(getattr(employee, 'employee_name', "")),
            'id_number': format_text(getattr(employee, 'id_number', "")),
            'address': format_text(getattr(employee, 'address', "")),
            'city': format_text(getattr(employee, 'city', "")),
            'postal_code': format_text(getattr(employee, 'postal_code', "")),
            'phone': format_text(getattr(employee, 'phone', "")),
            'email': format_text(getattr(employee, 'email', "")),
            'start_date': format_text(getattr(employee, 'start_date', "")),
            'date_of_birth': format_text(getattr(employee, 'date_of_birth', "")),
            'bank_number': format_text(getattr(employee, 'bank_number', "")),
            'branch_number': format_text(getattr(employee, 'branch_number', "")),
            'account_number': format_text(getattr(employee, 'account_number', "")),
            'hourly_rate': format_currency(getattr(employee, 'hourly_rate', 0.0)),
            'total_work_days': format_currency(getattr(employee, 'total_work_days', 0.0)),
            'totals_lunch_value': format_currency(getattr(employee, 'totals_lunch_value', 0.0)),
            'total_missing_hours': format_hours(getattr(employee, 'total_missing_hours', 0.0)),
            'mobile_value': format_currency(getattr(employee, 'mobile_value', 0.0)),
            'clothing_value': format_currency(getattr(employee, 'clothing_value', 0.0)),
            'lunch_value': format_currency(getattr(employee, 'lunch_value', 0.0)),
            'cars_value': format_currency(getattr(employee, 'cars_value', 0.0)),
            'advance_payment_salary': format_currency(getattr(employee, 'advance_payment_salary', 0.0)),
            'monthly_city_tax_tops': format_currency(getattr(employee, 'monthly_city_tax_tops', 0.0)),
            'city_value_percentage': format_percentage(getattr(employee, 'city_value_percentage', 0.0)),
            'final_city_tax_benefit': format_currency(getattr(employee, 'final_city_tax_benefit', 0.0)),
            'basic_salary': format_currency(getattr(employee, 'basic_salary', 0.0)),
            'additional_payments': format_currency(getattr(employee, 'additional_payments', 0.0)),
            'net_value': format_currency(getattr(employee, 'net_value', 0.0)),
            'gross_salary': format_currency(getattr(employee, 'gross_salary', 0.0)),
            'gross_taxable': format_currency(getattr(employee, 'gross_taxable', 0.0)),
            'above_ceiling_value': format_currency(getattr(employee, 'above_ceiling_value', 0.0)),
            'above_ceiling_fund': format_currency(getattr(employee, 'above_ceiling_fund', 0.0)),
            'above_ceiling_compensation': format_currency(getattr(employee, 'above_ceiling_compensation', 0.0)),
            'pension_fund': format_currency(getattr(employee, 'pension_fund', 0.0)),
            'compensation': format_currency(getattr(employee, 'compensation', 0.0)),
            'study_fund': format_currency(getattr(employee, 'study_fund', 0.0)),
            'disability': format_currency(getattr(employee, 'disability', 0.0)),
            'miscellaneous': format_currency(getattr(employee, 'miscellaneous', 0.0)),
            'national_insurance': format_currency(getattr(employee, 'national_insurance', 0.0)),
            'salary_tax': format_currency(getattr(employee, 'salary_tax', 0.0)),
            'total_employer_contributions': format_currency(getattr(employee, 'total_employer_contributions', 0.0)),
            'total_salary_cost': format_currency(getattr(employee, 'total_salary_cost', 0.0)),
            'employee_pension_fund': format_currency(getattr(employee, 'employee_pension_fund', 0.0)),
            'self_employed_pension_fund': format_currency(getattr(employee, 'self_employed_pension_fund', 0.0)),
            'study_fund_deductions': format_currency(getattr(employee, 'study_fund_deductions', 0.0)),
            'miscellaneous_deductions': format_currency(getattr(employee, 'miscellaneous_deductions', 0.0)),
            'national_insurance_deductions': format_currency(getattr(employee, 'national_insurance_deductions', 0.0)),
            'health_insurance_deductions': format_currency(getattr(employee, 'health_insurance_deductions', 0.0)),
            'income_tax': format_currency(getattr(employee, 'income_tax', 0.0)),
            'income_tax_before_credit': format_currency(getattr(employee, 'income_tax_before_credit', 0.0)),
            'tax_point_child': format_percentage(getattr(employee, 'tax_point_child', 0.0)),
            'tax_credit_points': format_percentage(getattr(employee, 'tax_credit_points', 0.0)),
            'amount_tax_credit_points_monthly': format_currency(getattr(employee, 'amount_tax_credit_points_monthly', 0.0)),
            'tax_level_precente': format_percentage(getattr(employee, 'tax_level_precente', 0.0)),
            'total_salary_pension_funds': format_currency(getattr(employee, 'total_salary_pension_funds', 0.0)),
            'total_deductions': format_currency(getattr(employee, 'total_deductions', 0.0)),
            'net_payment': format_currency(getattr(employee, 'net_payment', 0.0)),
            'employee_pension_fund_yearly': format_currency(getattr(employee, 'employee_pension_fund_yearly', 0.0)),
            'self_employed_pension_fund_yearly': format_currency(getattr(employee, 'self_employed_pension_fund_yearly', 0.0)),
            'study_fund_deductions_yearly': format_currency(getattr(employee, 'study_fund_deductions_yearly', 0.0)),
            'miscellaneous_deductions_yearly': format_currency(getattr(employee, 'miscellaneous_deductions_yearly', 0.0)),
            'national_insurance_deductions_yearly': format_currency(getattr(employee, 'national_insurance_deductions_yearly', 0.0)),
            'health_insurance_deductions_yearly': format_currency(getattr(employee, 'health_insurance_deductions_yearly', 0.0)),
            'income_tax_yearly': format_currency(getattr(employee, 'income_tax_yearly', 0.0)),
            'amount_tax_credit_points_monthly_yearly': format_currency(getattr(employee, 'amount_tax_credit_points_monthly_yearly', 0.0)),
            'final_city_tax_benefit_yearly': format_currency(getattr(employee, 'final_city_tax_benefit_yearly', 0.0)),
            'pension_fund_yearly': format_currency(getattr(employee, 'pension_fund_yearly', 0.0)),
            'compensation_yearly': format_currency(getattr(employee, 'compensation_yearly', 0.0)),
            'study_fund_yearly': format_currency(getattr(employee, 'study_fund_yearly', 0.0)),
            'disability_yearly': format_currency(getattr(employee, 'disability_yearly', 0.0)),
            'miscellaneous_yearly': format_currency(getattr(employee, 'miscellaneous_yearly', 0.0)),
            'national_insurance_yearly': format_currency(getattr(employee, 'national_insurance_yearly', 0.0)),
            'salary_tax_yearly': format_currency(getattr(employee, 'salary_tax_yearly', 0.0)),          
            'total_employer_contributions_yearly': format_currency(getattr(employee, 'total_employer_contributions_yearly', 0.0)),          
            'total_salary_cost_yearly': format_currency(getattr(employee, 'total_salary_cost_yearly', 0.0)),          
            'sick_days_salary_yearly': format_currency(getattr(employee, 'sick_days_salary_yearly', 0.0)),
            'vacation_days_salary_yearly': format_currency(getattr(employee, 'vacation_days_salary_yearly', 0.0)),
            'sick_days_balance_yearly': format_currency(getattr(employee, 'sick_days_balance_yearly', 0.0)),
            'vacation_balance_yearly': format_currency(getattr(employee, 'vacation_balance_yearly', 0.0)),
            'gross_taxable_yearly': format_currency(getattr(employee, 'gross_taxable_yearly', 0.0)),
            'thirteenth_salary': format_currency(getattr(employee, 'thirteenth_salary', 0.0)),
            'work_percent': format_currency(getattr(employee, 'work_percent', 0.0)),
            'sick_days_salary': format_currency(getattr(employee, 'sick_days_salary', 0.0)),
            'vacation_days_salary': format_currency(getattr(employee, 'vacation_days_salary', 0.0)),
            'sick_days_entitlement': format_currency(getattr(employee, 'sick_days_entitlement', 0.0)),
            'vacation_days_entitlement': format_currency(getattr(employee, 'vacation_days_entitlement', 0.0)),
            'final_extra_hours_weekend': format_currency(getattr(employee, 'final_extra_hours_weekend', 0.0)),
            'final_extra_hours_regular': format_currency(getattr(employee, 'final_extra_hours_regular', 0.0)),
            'food_break_unpaid_salary': format_currency(getattr(employee, 'food_break_unpaid_salary', 0.0)),
            'hours125_regular_salary': format_currency(getattr(employee, 'hours125_regular_salary', 0.0)),
            'hours150_regular_salary': format_currency(getattr(employee, 'hours150_regular_salary', 0.0)),
            'hours150_holidays_saturday_salary': format_currency(getattr(employee, 'hours150_holidays_saturday_salary', 0.0)),
            'hours175_holidays_saturday_salary': format_currency(getattr(employee, 'hours175_holidays_saturday_salary', 0.0)),
            'hours200_holidays_saturday_salary': format_currency(getattr(employee, 'hours200_holidays_saturday_salary', 0.0)),
            'employee_number': format_text(getattr(employee, 'employee_number', "")),
            'marital_status': format_text(getattr(employee, 'marital_status', "")),
            'work_apartment': format_text(getattr(employee, 'work_apartment', "")),
            'hospital': format_text(getattr(employee, 'hospital', "")),
            'social_number': format_text(getattr(employee, 'social_number', "")),
            'irs_status': format_text(getattr(employee, 'irs_status', "")),
            'contract_status': format_text(getattr(employee, 'contract_status', "")),
            'tax_credit_points': format_text(getattr(employee, 'tax_credit_points', "")),
            'tax_point_child': format_text(getattr(employee, 'tax_point_child', "")),
            'message': format_text(getattr(employee, 'message', ""))
        }

        # ----------------------
        # Build hoursData
        # ----------------------

        dailyFields = [
            'date', 'day', 'saturday', 'holiday', 'start-time', 'end-time',
            'hours-calculated', 'hours-calculated-regular-day', 'total-extra-hours-regular-day',
            'extra-hours125-regular-day', 'extra-hours150-regular-day', 'hours-holidays-day',
            'extra-hours150-holidays-saturday', 'extra-hours175-holidays-saturday', 'extra-hours200-holidays-saturday',
            'sick-day', 'day-off', 'food-break', 'final-totals-hours', 'calc1', 'calc2', 'calc3',
            'work-day', 'missing-work-day', 'advance-payment',
        ]

        monthlyFields = [
            "hours-calculated-monthly", "hours-calculated-regular-day-monthly", "total-extra-hours-regular-day-monthly",
            "extra-hours125-regular-day-monthly", "extra-hours150-regular-day-monthly", "hours-holidays-day-monthly",
            "extra-hours150-holidays-saturday-monthly", "extra-hours175-holidays-saturday-monthly",
            "extra-hours200-holidays-saturday-monthly", "sick-day-monthly", "day-off-monthly",
            "food-break-monthly", "final-totals-hours-monthly", "calc1-monthly", "calc2-monthly",
            "calc3-monthly", "work-day-monthly", "missing-work-day-monthly", "advance-payment-monthly"
        ]

        paidFields = [
            "hours-calculated-paid", "hours-calculated-regular-day-paid", "total-extra-hours-regular-day-paid",
            "extra-hours125-regular-day-paid", "extra-hours150-regular-day-paid", "hours-holidays-day-paid",
            "extra-hours150-holidays-saturday-paid", "extra-hours175-holidays-saturday-paid",
            "extra-hours200-holidays-saturday-paid", "sick-day-paid", "day-off-paid",
            "food-break-unpaid", "final-totals-hours-paid", "calc1-paid", "calc2-paid", "calc3-paid",
            "final-totals-lunch-value-paid", "final-total-extra-hours-weekend-monthly", "advance-payment-paid"
        ]

        # Query HoursData rows for this employee/month/year
        hours_rows = HoursData.query.filter_by(
            employee_id=employee_id,
            employeeMonth=month,
            employeeYear=year
        ).all()


        existing_record_found = len(hours_rows) > 0
        employee_data['existing_record_found'] = existing_record_found

        work_day_entries = []
        monthly_totals = {}
        paid_totals = {}

        for row in hours_rows:
            row_dict = row.to_dict()

            # Daily rows
            if row_dict.get('date'):
                entry = {field: row_dict.get(field, '') for field in dailyFields}
                work_day_entries.append(entry)

            # Monthly totals
            for f in monthlyFields:
                if row_dict.get(f) not in [None, ""]:
                    monthly_totals = {field: row_dict.get(field, '') for field in monthlyFields}
                    break

            # Paid totals
            for f in paidFields:
                if row_dict.get(f) not in [None, ""]:
                    paid_totals = {field: row_dict.get(field, '') for field in paidFields}
                    break

        # Fallbacks for UI (לא לזיהוי אם יש שעות, רק להצגה)
        if not work_day_entries:
            work_day_entries = [{field: "" for field in dailyFields}]
        if not monthly_totals:
            monthly_totals = {field: "" for field in monthlyFields}
        if not paid_totals:
            paid_totals = {field: "" for field in paidFields}

        employee_data['hours'] = {
            "work_day_entries": work_day_entries,
            "monthly_totals": monthly_totals,
            "paid_totals": paid_totals
        }

        return jsonify(employee_data)

    except Exception as e:
        return jsonify({'error': f'שגיאה: {str(e)}'}), 500

# ----------------------
# Get Employee Data For Save Session Storage Data: Form Page
# ----------------------

@app.route('/get_employee_data')
@login_required
def get_employee_data():
    employee_id = request.args.get('employee_id', '').strip()
    month = request.args.get('employeeMonth', '').strip()
    year = request.args.get('employeeYear', '').strip()

    if not employee_id or not month or not year:
        return jsonify({'error': 'Missing parameters'}), 400

    employee = EmployeeData.query.get(employee_id)
    if not employee:
        return jsonify({'error': 'Employee not found'}), 404

    date_key = f"{month}/{year}"

    # ----------------------
    # BASIC EMPLOYEE DATA
    # ----------------------
    employee_data = {
        'employee_id': employee_id,
        'employee_name': employee.employee_name,
        'employeeMonth': month,
        'employeeYear': year,
        'date': date_key,
        'id_number': employee.id_number,
        'address': employee.address,
        'city': employee.city,
        'postal_code': employee.postal_code,
        'phone': employee.phone,
        'email': employee.email,
        'start_date': employee.start_date,
        'date_of_birth': employee.date_of_birth,
        'bank_number': employee.bank_number,
        'branch_number': employee.branch_number,
        'account_number': employee.account_number,
        'hourly_rate': employee.hourly_rate,
        'total_work_days': employee.total_work_days,
        'totals_lunch_value': employee.totals_lunch_value,
        'total_missing_hours': employee.total_missing_hours,
        'tax_credit_points': employee.tax_credit_points,
        'monthly_city_tax_tops': employee.monthly_city_tax_tops,
        'city_value_percentage': employee.city_value_percentage,
        'final_city_tax_benefit': employee.final_city_tax_benefit,
        'basic_salary': employee.basic_salary,
        'additional_payments': employee.additional_payments,
        'cars_value': employee.cars_value,
        'net_value': employee.net_value,
        'gross_salary': employee.gross_salary,
        'above_ceiling_value': employee.above_ceiling_value,
        'above_ceiling_fund': employee.above_ceiling_fund,
        'above_ceiling_compensation': employee.above_ceiling_compensation,
        'gross_taxable': employee.gross_taxable,
        'pension_fund': employee.pension_fund,
        'compensation': employee.compensation,
        'study_fund': employee.study_fund,
        'disability': employee.disability,
        'miscellaneous': employee.miscellaneous,
        'national_insurance': employee.national_insurance,
        'salary_tax': employee.salary_tax,
        'total_employer_contributions': employee.total_employer_contributions,
        'total_salary_cost': employee.total_salary_cost,
        'employee_pension_fund': employee.employee_pension_fund,
        'self_employed_pension_fund': employee.self_employed_pension_fund,
        'study_fund_deductions': employee.study_fund_deductions,
        'miscellaneous_deductions': employee.miscellaneous_deductions,
        'national_insurance_deductions': employee.national_insurance_deductions,
        'health_insurance_deductions': employee.health_insurance_deductions,
        'income_tax': employee.income_tax,
        'advance_payment_salary': employee.advance_payment_salary,
        'total_deductions': employee.total_deductions,
        'net_payment': employee.net_payment,
        'employee_pension_fund_yearly': employee.employee_pension_fund_yearly,
        'self_employed_pension_fund_yearly': employee.self_employed_pension_fund_yearly,
        'study_fund_deductions_yearly': employee.study_fund_deductions_yearly,
        'miscellaneous_deductions_yearly': employee.miscellaneous_deductions_yearly,
        'national_insurance_deductions_yearly': employee.national_insurance_deductions_yearly,
        'health_insurance_deductions_yearly': employee.health_insurance_deductions_yearly,
        'income_tax_yearly': employee.income_tax_yearly,
        'amount_tax_credit_points_monthly_yearly': employee.amount_tax_credit_points_monthly_yearly,
        'final_city_tax_benefit_yearly': employee.final_city_tax_benefit_yearly,
        'pension_fund_yearly': employee.pension_fund_yearly,
        'compensation_yearly': employee.compensation_yearly,
        'study_fund_yearly': employee.study_fund_yearly,
        'disability_yearly': employee.disability_yearly,
        'miscellaneous_yearly': employee.miscellaneous_yearly,
        'national_insurance_yearly': employee.national_insurance_yearly,
        'salary_tax_yearly': employee.salary_tax_yearly,
        'total_employer_contributions_yearly': employee.total_employer_contributions_yearly,
        'total_salary_cost_yearly': employee.total_salary_cost_yearly,
        'sick_days_salary_yearly': employee.sick_days_salary_yearly,
        'vacation_days_salary_yearly': employee.vacation_days_salary_yearly,
        'sick_days_balance_yearly': employee.sick_days_balance_yearly,
        'vacation_balance_yearly': employee.vacation_balance_yearly,
        'gross_taxable_yearly': employee.gross_taxable_yearly,
        'tax_level_precente': employee.tax_level_precente,
        'income_tax_before_credit': employee.income_tax_before_credit,
        'amount_tax_credit_points_monthly': employee.amount_tax_credit_points_monthly,
        'thirteenth_salary': employee.thirteenth_salary,
        'work_percent': employee.work_percent,
        'sick_days_salary': employee.sick_days_salary,
        'vacation_days_salary': employee.vacation_days_salary,
        'sick_days_entitlement': employee.sick_days_entitlement,
        'vacation_days_entitlement': employee.vacation_days_entitlement,
        'final_extra_hours_weekend': employee.final_extra_hours_weekend,
        'final_extra_hours_regular': employee.final_extra_hours_regular,
        'food_break_unpaid_salary': employee.food_break_unpaid_salary,
        'hours125_regular_salary': employee.hours125_regular_salary,
        'hours150_regular_salary': employee.hours150_regular_salary,
        'hours150_holidays_saturday_salary': employee.hours150_holidays_saturday_salary,
        'hours175_holidays_saturday_salary': employee.hours175_holidays_saturday_salary,
        'hours200_holidays_saturday_salary': employee.hours200_holidays_saturday_salary,
        'mobile_value': employee.mobile_value,
        'clothing_value': employee.clothing_value,
        'contract_status': employee.contract_status,
        'lunch_value': employee.lunch_value,
        'total_salary_pension_funds': employee.total_salary_pension_funds,
        'employee_number': employee.employee_number,
        'marital_status': employee.marital_status,
        'message': employee.message
    }

    # ----------------------
    # ADD HOURS TABLE
    # ----------------------

    hours_rows = HoursData.query.filter_by(
        employee_id=employee_id,
        employeeMonth=month,
        employeeYear=year
    ).all()

    employee_data['existing_record_found'] = len(hours_rows) > 0

    # FULL HOURS TABLE (ALL FIELDS)
    dailyFields = [
        'date', 'day', 'saturday', 'holiday',
        'start_time', 'end_time',
        'hours_calculated', 'hours_calculated_regular_day', 'total_extra_hours_regular_day',
        'extra_hours125_regular_day', 'extra_hours150_regular_day', 'hours_holidays_day',
        'extra_hours150_holidays_saturday', 'extra_hours175_holidays_saturday', 'extra_hours200_holidays_saturday',
        'sick_day', 'day_off', 'food_break',
        'final_totals_hours', 'calc1', 'calc2', 'calc3',
        'work_day', 'missing_work_day', 'advance_payment'
    ]

    monthlyFields = [
        'hours_calculated_monthly', 'hours_calculated_regular_day_monthly', 'total_extra_hours_regular_day_monthly',
        'extra_hours125_regular_day_monthly', 'extra_hours150_regular_day_monthly', 'hours_holidays_day_monthly',
        'extra_hours150_holidays_saturday_monthly', 'extra_hours175_holidays_saturday_monthly',
        'extra_hours200_holidays_saturday_monthly', 'sick_day_monthly', 'day_off_monthly',
        'food_break_monthly', 'final_totals_hours_monthly', 'calc1_monthly', 'calc2_monthly',
        'calc3_monthly', 'work_day_monthly', 'missing_work_day_monthly', 'advance_payment_monthly'
    ]

    paidFields = [
        'hours_calculated_paid', 'hours_calculated_regular_day_paid', 'total_extra_hours_regular_day_paid',
        'extra_hours125_regular_day_paid', 'extra_hours150_regular_day_paid', 'hours_holidays_day_paid',
        'extra_hours150_holidays_saturday_paid', 'extra_hours175_holidays_saturday_paid',
        'extra_hours200_holidays_saturday_paid', 'sick_day_paid', 'day_off_paid',
        'food_break_unpaid', 'final_totals_hours_paid', 'calc1_paid', 'calc2_paid', 'calc3_paid',
        'final_totals_lunch_value_paid', 'final_total_extra_hours_weekend_monthly', 'advance_payment_paid'
    ]

    daily_rows = []
    monthly_rows = []
    paid_rows = []

    for row in hours_rows:
        r = row.to_dict()

        if any(r.get(f) not in [None, "", "0"] for f in dailyFields):
            daily_rows.append(r)
            continue

        if any(r.get(f) not in [None, "", "0"] for f in monthlyFields):
            monthly_rows.append(r)
            continue

        if any(r.get(f) not in [None, "", "0"] for f in paidFields):
            paid_rows.append(r)
            continue

    employee_data["hours_data"] = {
        "daily": daily_rows,
        "monthly": monthly_rows,
        "paid": paid_rows
    }

    return jsonify(employee_data)

# ----------------------
#   Build All Customer Form
# ----------------------

@app.route('/customer_form', methods=['GET', 'POST'])
@login_required
def customer_form():
    if request.method == 'POST':
        # Get form data and validate
        date_str = request.form['date']
        if not date_str:
            flash('תאריך הוא שדה חובה', 'error')
            return redirect(url_for('customer_form'))

        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%d/%m/%Y')  # Corrected format string

        customer_name = request.form.get('customer_name')
        existing_customer = CustomerForm.query.filter_by(customer_name=customer_name).first()

        if existing_customer:
            flash('הלקוח כבר קיים, אנא עדכן את הפרטים', 'error')
            return redirect(url_for('update_customer', customer_id=existing_customer.id))

        customer_id = request.form.get('customer_id')
        if customer_id:
            # Update existing customer
            customer = CustomerForm.query.get(customer_id)
            customer.date = formatted_date
            customer.customer_name = request.form.get('customer_name')
            customer.id_number = request.form.get('id_number')
            customer.address = request.form.get('address')
            customer.city = request.form.get('city')
            customer.postal_code = request.form.get('postal_code')
            customer.phone = request.form.get('phone')
            customer.clothing_value = request.form.get('clothing_value')
            customer.cars_value = request.form.get('cars_value')
            customer.email = request.form.get('email')
            customer.start_date = request.form.get('start_date')
            customer.bank_number = request.form.get('bank_number')
            customer.branch_number = request.form.get('branch_number')
            customer.account_number = request.form.get('account_number')
            customer.lunch_value = request.form.get('lunch_value')
            customer.mobile_value = request.form.get('mobile_value')
            customer.hourly_rate = request.form.get('hourly_rate')
            customer.customer_number = request.form.get('customer_number')
            customer.thirteenth_salary = request.form.get('thirteenth_salary')
            customer.message = request.form.get('message')
            customer.work_apartment = request.form.get('work_apartment')
            customer.work_percent = request.form.get('work_percent')
            customer.marital_status = request.form.get('marital_status')
            customer.tax_point = request.form.get('tax_point')
            customer.hospital = request.form.get('hospital')
            customer.social_number = request.form.get('social_number')
            customer.irs_status = request.form.get('irs_status')
            customer.contract_status = request.form.get('contract_status')
            customer.tax_point_child = request.form.get('tax_point_child')

            db.session.commit()
            flash('הנתונים עודכנו בהצלחה!', 'success')
        else:
            # Add new customer
            new_customer = CustomerForm(
                date=formatted_date,
                customer_name=request.form.get('customer_name'),
                id_number=request.form.get('id_number'),
                address=request.form.get('address'),
                city=request.form.get('city'),
                postal_code=request.form.get('postal_code'),
                phone=request.form.get('phone'),
                clothing_value=request.form.get('clothing_value'),
                cars_value=request.form.get('cars_value'),
                email=request.form.get('email'),
                start_date=request.form.get('start_date'),
                bank_number=request.form.get('bank_number'),
                branch_number=request.form.get('branch_number'),
                account_number=request.form.get('account_number'),
                lunch_value=request.form.get('lunch_value'),
                mobile_value=request.form.get('mobile_value'),
                hourly_rate=request.form.get('hourly_rate'),
                customer_number=request.form.get('customer_number'),
                thirteenth_salary=request.form.get('thirteenth_salary'),
                message=request.form.get('message'),
                work_apartment=request.form.get('work_apartment'),
                work_percent=request.form.get('work_percent'),
                marital_status=request.form.get('marital_status'),
                tax_point=request.form.get('tax_point'),
                hospital=request.form.get('hospital'),
                social_number=request.form.get('social_number'),
                irs_status=request.form.get('irs_status'),
                contract_status = request.form.get('contract_status'),
                tax_point_child = request.form.get('tax_point_child')
            )

            db.session.add(new_customer)
            db.session.commit()
            flash('הנתונים נשמרו בהצלחה!', 'success')

        return redirect(url_for('customer_data'))

    customer_id = request.args.get('customer_id')
    customer = CustomerForm.query.get(customer_id) if customer_id else None
    return render_template('customer_form.html', customer=customer)

@app.route('/customer_data', methods=['GET'])
@login_required
def customer_data():
    customers = CustomerForm.query.all()
    return render_template('customer_data.html', customers=customers)

@app.route('/update_customer/<int:customer_id>', methods=['GET', 'POST'])
@login_required
def update_customer(customer_id):
    customer = CustomerForm.query.get(customer_id)
    if request.method == 'POST':
        # Update customer information
        customer.date = request.form.get('date')
        customer.customer_name = request.form.get('customer_name')
        customer.id_number = request.form.get('id_number')
        customer.address = request.form.get('address')
        customer.city = request.form.get('city')
        customer.postal_code = request.form.get('postal_code')
        customer.phone = request.form.get('phone')
        customer.clothing_value = request.form.get('clothing_value')
        customer.cars_value = request.form.get('cars_value')
        customer.email = request.form.get('email')
        customer.start_date = request.form.get('start_date')
        customer.bank_number = request.form.get('bank_number')
        customer.branch_number = request.form.get('branch_number')
        customer.account_number = request.form.get('account_number')
        customer.lunch_value = request.form.get('lunch_value')
        customer.mobile_value = request.form.get('mobile_value')
        customer.hourly_rate = request.form.get('hourly_rate')
        customer.customer_number = request.form.get('customer_number')
        customer.thirteenth_salary = request.form.get('thirteenth_salary')
        customer.message = request.form.get('message')
        customer.work_apartment = request.form.get('work_apartment')
        customer.work_percent = request.form.get('work_percent')
        customer.marital_status = request.form.get('marital_status')
        customer.tax_point = request.form.get('tax_point')
        customer.hospital = request.form.get('hospital')
        customer.social_number = request.form.get('social_number')
        customer.irs_status = request.form.get('irs_status')
        customer.contract_status = request.form.get('contract_status')
        customer.tax_point_child = request.form.get('tax_point_child')

        db.session.commit()
        flash('הנתונים עודכנו בהצלחה!', 'success')
        return redirect(url_for('customer_data'))

    return render_template('update_customer.html', customer=customer)
 
@app.route('/search_customer', methods=['GET', 'POST'])
@login_required
def search_customer():
    search_name = request.form.get('search_name') if request.method == 'POST' else request.args.get('search_name')
    search_results = CustomerForm.query.filter(CustomerForm.customer_name.ilike(f'%{search_name}%')).all() if search_name else []
    all_customers = CustomerForm.query.all()
    months = ['ינואר', 'פברואר', 'מרץ', 'אפריל', 'מאי', 'יוני', 'יולי', 'אוגוסט', 'ספטמבר', 'אוקטובר', 'נובמבר', 'דצמבר']
    years = list(range(2020, 2031))
    days_data = get_days_in_month(2024, 1)

    customer = search_results[0] if search_results else None

    return render_template('customer_form.html', months=months, years=years, days_data=days_data, customers=search_results, all_customers=all_customers, customer=customer)

@app.route('/clear_search_results_customer', methods=['POST'])
@login_required
def clear_search_results_customer():
    months = ['ינואר', 'פברואר', 'מרץ', 'אפריל', 'מאי', 'יוני', 'יולי', 'אוגוסט', 'ספטמבר', 'אוקטובר', 'נובמבר', 'דצמבר']
    years = list(range(2020, 2031))
    days_data = get_days_in_month(2024, 1)
    all_customers = CustomerForm.query.all()

    customer = None

    flash('החיפוש נוקה בהצלחה!', 'info')  # Added flash message

    return render_template('customer_form.html', months=months, years=years, days_data=days_data, customers=[], all_customers=all_customers, customer=customer)

# ----------------------
# Get Tax Credit Simulator: Form Page
# ----------------------

@app.route('/tax_credit_simulator', methods=['GET', 'POST'])
@login_required
def tax_credit_simulator():
    tax_credits = 0

    if request.method == 'POST':
        # Collect form data
        is_israeli_resident = request.form.get('is_israeli_resident') == 'on'
        gender = request.form.get('gender', '')
        is_teenager = request.form.get('is_teenager') == 'on'
        is_married = request.form.get('is_married') == 'on'
        is_special_situation = request.form.get('is_special_situation') == 'on'
        has_children = request.form.get('has_children') == 'yes'
        married_to_widower = request.form.get('married_to_widower') == 'yes'
        single_parent = request.form.get('single_parent') == 'yes'
        separate_household = request.form.get('separate_household') == 'yes'
        single_parent_no_spouse = request.form.get('single_parent_no_spouse') == 'yes'
        paying_child_support = request.form.get('paying_child_support') == 'yes'
        remarried_paying_alimony = request.form.get('remarried_paying_alimony') == 'yes'
        newborn_count = int(request.form.get('newborn_count') or 0)
        age_1_count = int(request.form.get('age_1_count') or 0)
        age_2_count = int(request.form.get('age_2_count') or 0)
        age_3_count = int(request.form.get('age_3_count') or 0)
        age_4_count = int(request.form.get('age_4_count') or 0)
        age_5_count = int(request.form.get('age_5_count') or 0)
        age_6_17_count = int(request.form.get('age_6_17_count') or 0)
        age_18_count = int(request.form.get('age_18_count') or 0)
        children_not_in_custody = int(request.form.get('children_not_in_custody') or 0)

        # Calculate tax credits
        if is_israeli_resident: tax_credits += 2.25
        if gender == 'female': tax_credits += 0.5
        if is_teenager: tax_credits += 1
        if is_special_situation: tax_credits += 1
        if has_children: tax_credits += 0.5
        if married_to_widower: tax_credits += 1
        if single_parent: tax_credits += 1
        if separate_household: tax_credits += 1
        if single_parent_no_spouse: tax_credits += 1
        if paying_child_support: tax_credits += 1
        if remarried_paying_alimony: tax_credits += 1

        # Children by age
        tax_credits += 2.5 * newborn_count
        tax_credits += 4.5 * age_1_count
        tax_credits += 4.5 * age_2_count
        tax_credits += 3.5 * age_3_count
        tax_credits += 2.5 * age_4_count
        tax_credits += 2.5 * age_5_count
        tax_credits += 2.0 * age_6_17_count
        tax_credits += 0.5 * age_18_count
        tax_credits += 2.5 * children_not_in_custody

        # Save to database
        new_tax_credit = TaxCredit(
            is_israeli_resident=is_israeli_resident,
            gender=gender,
            is_teenager=is_teenager,
            is_married=is_married,
            is_special_situation=is_special_situation,
            has_children=has_children,
            married_to_widower=married_to_widower,
            single_parent=single_parent,
            separate_household=separate_household,
            single_parent_no_spouse=single_parent_no_spouse,
            paying_child_support=paying_child_support,
            remarried_paying_alimony=remarried_paying_alimony,
            newborn_count=newborn_count,
            age_1_count=age_1_count,
            age_2_count=age_2_count,
            age_3_count=age_3_count,
            age_4_count=age_4_count,
            age_5_count=age_5_count,
            age_6_17_count=age_6_17_count,
            age_18_count=age_18_count,
            children_not_in_custody=children_not_in_custody,
            total_tax_credits=tax_credits
        )

        db.session.add(new_tax_credit)
        db.session.commit()

        flash('Tax credits have been successfully calculated and saved!', 'success')

        #  Render template directly with result
        return render_template('tax_credit_simulator.html', tax_credits=tax_credits)

    # GET request — show empty form
    return render_template('tax_credit_simulator.html', tax_credits=tax_credits)
 
# ----------------------
# Protected Route
# ----------------------
@app.route('/get_days/<int:year>/<int:month>')
@login_required
def get_days(year, month):
    days_data = get_days_in_month(year, month)
    return jsonify(days_data)

# ----------------------
# Protected Socket Events
# ----------------------
@socketio.on('connect')
def handle_connect():
    if not current_user.is_authenticated:
        print('Unauthorized connection attempt')
        disconnect()
        return
    print(f'Client connected: {current_user.username}')
    # emit('response', {'message': 'Connected to server'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('message')
def handle_message(data):
    if not current_user.is_authenticated:
        print('Unauthorized message attempt')
        disconnect()
        return
    print(f'Received message from {current_user.username}: {data}')
    emit('response', {'message': 'Message received'})

# ----------------------
# Run it
# ----------------------
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port, debug=True)

