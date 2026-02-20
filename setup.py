from uuid import uuid4
import os, csv, json, logging, calendar, re, secrets
from functools import wraps
import subprocess
import sys
from flask import Flask, render_template, request, redirect, url_for, jsonify, Response, session, flash
import json
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy import Text
from flask_migrate import Migrate
from flask_socketio import SocketIO, emit
from flask_mail import Mail, Message
import pandas as pd
import numpy as np
import openpyxl, xlsxwriter
from sqlalchemy import func
from sqlalchemy import Text
import time
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# ──────────────────────────────────────────────
# Load environment variables first
# ──────────────────────────────────────────────
load_dotenv()

# ──────────────────────────────────────────────
# Import custom modules
# ──────────────────────────────────────────────
from database import db, EmployeeData, MonthlyRecord, HoursData, PasswordResetToken, CustomerForm, TaxCredit, BankAccount , Invoice , Product, Timesheet, User
from data import get_employees, add_employee

# ──────────────────────────────────────────────
# Flask App Setup
# ──────────────────────────────────────────────
app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', str(uuid4()))
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Mail configuration loaded from .env
app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.office365.com")
app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")
mail = Mail(app)

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
socketio = SocketIO(app)

# ──────────────────────────────────────────────
# Utility
# ──────────────────────────────────────────────
def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0

def run_command(command, label=None):
    print(f"\n {label or 'Running'}: {command}")
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        print(f" Failed: {command}")
        sys.exit(result.returncode)

# ──────────────────────────────────────────────
# Setup Tasks
# ──────────────────────────────────────────────

def create_gitignore():
    sections = {
        " Skip runtime-generated data": [
            "*.csv", "*.log", "*/**/*.csv", "*/**/*.log"
        ],
        " Skip app data folders": [
            "HoursCard/", "HoursCard/**/*.csv"
        ],
        " Python artifacts": [
            "__pycache__/", "*.pyc", "*.pyo", "*.pyd"
        ],
        " Virtual environments": [
            "env/", "venv/", "new_venv/"
        ],
        " Configs and secrets": [
            "*.db", ".env", "config.py", "instance/"
        ],
        " IDE & editor metadata": [
            ".vscode/", ".idea/", "migrations/"
        ],
        " OS-specific junk": [
            ".DS_Store", "Thumbs.db"
        ]
    }

    lines = []
    print(" Creating .gitignore with full sections:\n")

    for title, patterns in sections.items():
        print(f"{title}")
        for rule in patterns:
            print(f"  └─ {rule}")
            lines.append(rule)
        print()

    with open(".gitignore", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n ✅ .gitignore created with full protection.")

def setup_git(project_path):
    os.chdir(project_path)
    if not os.path.exists(".git"):
        run_command("git init", "Initializing Git")
        run_command("git add -A", "Staging all files")
        run_command('git commit -m "Initial clean setup"', "Committing")
    else:
        print(" Git already initialized")

def setup_virtualenv():
    if not os.path.exists("new_venv"):
        run_command("python -m venv new_venv", "Creating virtual environment")
    print(" ➜ To activate manually:")
    print("     Windows ➜ .\\new_venv\\Scripts\\activate")
    print("     Mac/Linux ➜ source new_venv/bin/activate")

def create_requirements():
    packages = [
        "flask", "flask-sqlalchemy", "psycopg2-binary", "flask-migrate", "flask-socketio",
        "flask-session", "flask-script", "python-socketio", "eventlet",
        "pandas", "openpyxl", "werkzeug", "Flask-Mail", "gunicorn",
        "python-dotenv", "xlsxwriter", "flask-login", "numpy", "flask-jwt-extended"
    ]

    with open("requirements.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(packages))
    print(" ✅ requirements.txt created successfully")

def install_packages():
    run_command("new_venv\\Scripts\\activate && python -m pip install --upgrade pip", "Upgrading pip")
    run_command("new_venv\\Scripts\\activate && pip install -r requirements.txt", "Installing packages")

def initialize_migrations():
    os.environ['FLASK_APP'] = os.path.join(project_path, 'main.py')
    os.environ['FLASK_ENV'] = 'development'
    if not os.path.exists('migrations'):
        run_command("flask db init", "Initializing migrations")

def run_auto_migrate():
    run_command('flask db migrate -m "Auto migration"', "Running migration")
    
    migration_dir = os.path.join("migrations", "versions")
    if os.path.exists(migration_dir):
        migration_files = sorted(
            [f for f in os.listdir(migration_dir) if f.endswith(".py")], reverse=True
        )

        if migration_files:
            file_path = os.path.join(migration_dir, migration_files[0])
            with open(file_path, "r") as f:
                content = f.read()
            if "Text()" in content and "from sqlalchemy import Text" not in content:
                content = content.replace(
                    "from alembic import op",
                    "from alembic import op\nfrom sqlalchemy import Text"
                )
                with open(file_path, "w") as f:
                    f.write(content)
                print(f" ✅ Patched missing 'Text' import in {migration_files[0]}")
    else:
        print(" ⚠️ Could not find migration directory — skipping patch.")

    run_command("flask db upgrade", "Upgrading database")

def create_database():
    if os.path.exists("create_db.py"):
        run_command("python create_db.py", "Creating database")

def init_database():
    if os.path.exists("init_db.py"):
        run_command("python init_db.py", "Initializing database")

def create_update_db_batch_file():
    with open("update_db.bat", "w") as f:
        f.write("@echo off\n")
        f.write("set FLASK_APP=main.py\n")
        f.write('flask db migrate -m "Auto migration"\n')
        f.write("flask db upgrade\n")
        f.write("pause\n")
    print(" ✅ update_db.bat created for future upgrades")

def launch_app():
    print(" 🚀 Launching your app with Socket.IO...")
    run_command(f'python {os.path.join(project_path, "main.py")}', "Starting Flask app")

# ──────────────────────────────────────────────
# Run All Steps (Your original project path)
# ──────────────────────────────────────────────
if __name__ == '__main__':
    print(" 🔧 Starting full setup...")
    project_path = r"C:\\Users\\AA\\Desktop\\App_salary\\HoursCard"
    os.chdir(project_path)

    create_requirements()
    setup_virtualenv()
    create_gitignore()
    install_packages()
    initialize_migrations()
    run_auto_migrate()
    create_database()
    init_database()
    create_update_db_batch_file()
    setup_git(project_path)
    launch_app()

# CLI support
if __name__ != "__main__":
    app = app
