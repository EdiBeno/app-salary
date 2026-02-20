import os
from dotenv import load_dotenv
from main import app, db

# 1. Load Environment Variables FIRST 
# This ensures Python knows if it's connecting to SQLite or Postgres
load_dotenv()

# 2. Explicitly import all models so SQLAlchemy "sees" them
# This prevents "Table not found" errors
from database import (
    db, EmployeeData, MonthlyRecord, HoursData, 
    PasswordResetToken, CustomerForm, TaxCredit, 
    BankAccount, Invoice, Product, Timesheet, User
)

def init_database():
    """
    Initializes the database based on the DB_CHOICE in your .env
    Works for both local SQLite and remote PostgreSQL.
    """
    try:
        with app.app_context():
            # Print the URI (hiding password) to verify where we are saving
            db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            masked_uri = db_uri.split('@')[-1] if '@' in db_uri else db_uri
            print(f"🔄 Attempting to initialize DB at: ...{masked_uri}")

            # 3. Create all tables defined in your models
            db.create_all()
            
            print("✅ Database tables created/synced successfully.")
            
            # 4. Optional: Check if a test query works
            # This proves the connection is actually alive
            user_count = db.session.query(User).count()
            print(f"📊 Current User count in DB: {user_count}")

    except Exception as e:
        print(f"❌ ERROR: Database initialization failed!")
        print(f"Details: {str(e)}")

if __name__ == '__main__':
    init_database()
