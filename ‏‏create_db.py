import os
from main import app, db  # ייבוא האפליקציה וה-db מהקובץ הראשי
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

# טעינת המשתנים מה-.env כדי לדעת באיזה DB להשתמש
load_dotenv()

# ייבוא כל המודלים (חשוב כדי ש-create_all יזהה אותם)
from database import (
    db, EmployeeData, MonthlyRecord, HoursData, PasswordResetToken, 
    CustomerForm, TaxCredit, BankAccount, Invoice, Product, Timesheet, User
)

def create_database():
    """
    מאתחל את בסיס הנתונים ויוצר את הטבלאות לפי הקונפיגורציה ב-main.
    """
    # אנחנו לא מגדירים כאן URI ידנית! 
    # הקוד ישתמש במה שמוגדר ב-app שייבאנו מ-main.py
    
    try:
        with app.app_context():  # כניסה להקשר של Flask
            print(f"🔄 Initializing tables on: {app.config['SQLALCHEMY_DATABASE_URI']}")
            
            # יצירת כל הטבלאות
            db.create_all()  
            
            print("✅ Database and tables created successfully!")
    except SQLAlchemyError as e:
        print(f"❌ Error creating database tables: {e}")
    except Exception as e:
        print(f"❌ General error: {e}")

if __name__ == '__main__':
    create_database()
