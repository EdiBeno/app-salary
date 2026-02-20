
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Date, DateTime, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.declarative import declarative_base
from datetime import time, datetime, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from typing import TypedDict

db = SQLAlchemy()

# -----------------------------
#  Regular User
# -----------------------------

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), nullable=True)
    password_hash = db.Column(db.String(256), nullable=True)  # ריק עד שהמשתמש קובע סיסמה

    #  customer / employee / owner
    role = db.Column(db.String(50), nullable=False, default='customer')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    is_active = db.Column(db.Boolean, default=True)  # פעיל / חסום
    access_expires_at = db.Column(db.DateTime, nullable=True)  # תוקף גישה (None = ללא הגבלה)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


    def has_valid_access(self):
        if not self.is_active:
            return False
        if self.access_expires_at is None:
            return True
        return datetime.utcnow() < self.access_expires_at

    def seconds_left(self):
        if self.access_expires_at is None:
            return None
        diff = (self.access_expires_at - datetime.utcnow()).total_seconds()
        return max(0, int(diff))

# -----------------------------
# Flask-Login required methods
# -----------------------------

    def get_id(self):
        return str(self.id)

# -----------------------------
#  Token Store for Clients
# -----------------------------

class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_tokens'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(128), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# -----------------------------
#  Employee Data
# -----------------------------

class EmployeeData(db.Model):
    __tablename__ = 'employee_data'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    user = db.relationship('User', backref='employee_profile')

    employee_name = db.Column(db.String(100), nullable=False)
    id_number = db.Column(db.String(50), unique=True, nullable=False)  # Social security

    employeeMonth = db.Column(db.String(2))       
    employeeYear = db.Column(db.String(4))        
    date = db.Column(db.String(10))                 
    month_result = db.Column(db.String(20))       
    save_date = db.Column(db.String(10))

    month_key = db.Column(db.String(7))  
    
    address = db.Column(db.String(100))
    city = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    phone = db.Column(db.String(20))
    mobile_value = db.Column(db.Float)
    clothing_value = db.Column(db.Float)
    cars_value = db.Column(db.Float)  
    email = db.Column(db.String(100))
    start_date = db.Column(db.String(10))
    date_of_birth = db.Column(db.String(10))
    monthly_city_tax_tops = db.Column(db.Float)
    bank_number = db.Column(db.String(20))
    branch_number = db.Column(db.String(20))
    account_number = db.Column(db.String(20))
    lunch_value = db.Column(db.Float)
    hourly_rate = db.Column(db.String(50))
    employee_number = db.Column(db.String(100))
    thirteenth_salary = db.Column(db.Float)
    message = db.Column(db.Text)
    work_apartment = db.Column(db.String(100))
    work_percent = db.Column(db.String(20))
    marital_status = db.Column(db.String(20))
    tax_credit_points = db.Column(db.String(20))
    hospital = db.Column(db.String(100))
    social_number = db.Column(db.String(20))
    irs_status = db.Column(db.String(20))
    contract_status = db.Column(db.String(20))
    tax_point_child = db.Column(db.String(20))

    # Tax and salary
    final_city_tax_benefit = db.Column(db.Float)  
    total_hours = db.Column(db.Float)
    basic_salary = db.Column(db.Float)
    additional_payments = db.Column(db.Float)
    net_value = db.Column(db.Float)
    gross_salary = db.Column(db.Float)
    above_ceiling_value = db.Column(db.Float)
    above_ceiling_fund = db.Column(db.Float)
    above_ceiling_compensation = db.Column(db.Float)
    gross_taxable = db.Column(db.Float)
    pension_fund = db.Column(db.Float)
    compensation = db.Column(db.Float)
    study_fund = db.Column(db.Float)
    disability = db.Column(db.Float)
    miscellaneous = db.Column(db.Float)
    national_insurance = db.Column(db.Float)
    total_employer_contributions = db.Column(db.Float)
    total_salary_cost = db.Column(db.Float)
    employee_pension_fund = db.Column(db.Float)
    self_employed_pension_fund = db.Column(db.Float)
    study_fund_deductions = db.Column(db.Float)
    miscellaneous_deductions = db.Column(db.Float)
    national_insurance_deductions = db.Column(db.Float)
    health_insurance_deductions = db.Column(db.Float)
    income_tax = db.Column(db.Float)
    total_deductions = db.Column(db.Float)
    net_payment = db.Column(db.Float)

    advance_payment_salary = db.Column(db.Float)

    #  Car-related fields
    car_value = db.Column(db.Float)  
    car_year = db.Column(db.String(10))  
    car_model = db.Column(db.String(50))  
    car_type = db.Column(db.String(50)) 

    #  City-related fields
    monthly_city_top_tax = db.Column(db.Float)  
    city_name = db.Column(db.String(100))  
    city_sign = db.Column(db.String(10))  
    city_value_percentage = db.Column(db.Float)  

    salary_tax = db.Column(db.Float)
    income_tax_before_credit = db.Column(db.Float, default=0.0)
    tax_level_precente = db.Column(db.Float, default=0.0)
    amount_tax_credit_points_monthly = db.Column(db.Float, default=0.0)
    total_salary_pension_funds = db.Column(db.Float, default=0.0)
    hours_table_data = db.Column(db.Text, nullable=True)
    total_work_days = db.Column(db.Float, default=0.0)
    totals_lunch_value = db.Column(db.Float, default=0.0)
    total_missing_hours = db.Column(db.Float, default=0.0)
    final_extra_hours_weekend = Column(Float, default=0.0)
    final_extra_hours_regular = Column(Float, default=0.0)
    food_break_unpaid_salary = Column(Float, default=0.0)

    hours125_regular_salary = Column(Float, default=0.0)
    hours150_regular_salary = Column(Float, default=0.0)
    hours150_holidays_saturday_salary = Column(Float, default=0.0)
    hours175_holidays_saturday_salary = Column(Float, default=0.0)
    hours200_holidays_saturday_salary = Column(Float, default=0.0)

    # Yearly Sick Days Vacation Fields
    sick_days_salary = db.Column(db.Float, default=0.0)
    vacation_days_salary = db.Column(db.Float, default=0.0)
    sick_days_salary_yearly = db.Column(db.Float, default=0.0)
    vacation_days_salary_yearly = db.Column(db.Float, default=0.0)
    sick_days_entitlement = db.Column(db.Float, default=0.0)
    vacation_days_entitlement = db.Column(db.Float, default=0.0)
    sick_days_balance_yearly = db.Column(db.Float, default=0.0)
    vacation_balance_yearly = db.Column(db.Float, default=0.0)
    gross_taxable_yearly = db.Column(db.Float, default=0.0)

    # Yearly Deduction Fields
    employee_pension_fund_yearly = db.Column(db.Float, default=0.0)
    self_employed_pension_fund_yearly = db.Column(db.Float, default=0.0)
    study_fund_deductions_yearly = db.Column(db.Float, default=0.0)
    miscellaneous_deductions_yearly = db.Column(db.Float, default=0.0)
    national_insurance_deductions_yearly = db.Column(db.Float, default=0.0)
    health_insurance_deductions_yearly = db.Column(db.Float, default=0.0)
    income_tax_yearly = db.Column(db.Float, default=0.0)
    amount_tax_credit_points_monthly_yearly = db.Column(db.Float, default=0.0)
    final_city_tax_benefit_yearly = db.Column(db.Float, default=0.0)

    # Yearly Employer Contribution Fields
    pension_fund_yearly = db.Column(db.Float, default=0.0)
    compensation_yearly = db.Column(db.Float, default=0.0)
    study_fund_yearly = db.Column(db.Float, default=0.0)
    disability_yearly = db.Column(db.Float, default=0.0)
    miscellaneous_yearly = db.Column(db.Float, default=0.0)
    national_insurance_yearly = db.Column(db.Float, default=0.0)
    salary_tax_yearly = db.Column(db.Float, default=0.0)
    total_employer_contributions_yearly = db.Column(db.Float, default=0.0)
    total_salary_cost_yearly = db.Column(db.Float, default=0.0)

    # Form 102 Monthly Fields
    employee_count = Column(Integer, default=0)
    total_gross = Column(Float, default=0.0)
    total_income_tax = Column(Float, default=0.0)
    total_ni_employee = Column(Float, default=0.0)
    total_health = Column(Float, default=0.0)
    total_study_fund_deductions = Column(Float, default=0.0)
    emp_pension = Column(Float, default=0.0)
    self_pension = Column(Float, default=0.0)
    final_emp_pension_combined = Column(Float, default=0.0)
    pension_val = Column(Float, default=0.0)
    comp_val = Column(Float, default=0.0)
    disability_val = Column(Float, default=0.0)
    total_employer_pension_combined = Column(Float, default=0.0)
    study_fund_val = Column(Integer, default=0)
    national_insurance_val = Column(Integer, default=0)
    final_emp_deductions_total = Column(Float, default=0.0)
    final_totals_income_tax = Column(Float, default=0.0)

    # Form B102 Monthly Fields
    regular_salary = db.Column(db.Float)
    reduced_salary = db.Column(db.Float)
    regular_count = db.Column(db.Integer)
    reduced_count = db.Column(db.Integer)
    total_salary = db.Column(db.Float)

    # Form 102 Monthly Fields
    eilat_regular_tax = db.Column(db.Float)
    eilat_benefit_20 = db.Column(db.Float)
    eilat_total_tax_after_benefit = db.Column(db.Float)
    controlling_salary = db.Column(db.Float)
    controlling_tax = db.Column(db.Float)
    outside_eilat_salary = db.Column(db.Float)
    outside_eilat_tax = db.Column(db.Float)
    total_tax_all = db.Column(db.Float)

    regularSalary = db.Column(db.Float)
    eilatRegularTax = db.Column(db.Float)
    eilatBenefit20 = db.Column(db.Float)
    eilatTotalTaxAfterBenefit = db.Column(db.Float)
    controllingSalary = db.Column(db.Float)
    controllingTax = db.Column(db.Float)
    outsideEilatSalary = db.Column(db.Float)
    outsideEilatTax = db.Column(db.Float)
    totalTaxAll = db.Column(db.Float)

    totalDisabilityVal = db.Column(db.Float)
    totalStudyFundVal = db.Column(db.Float)
    totalProvidentDeduction = db.Column(db.Float)
    totalEmpPension = db.Column(db.Float)
    totalSelfPension = db.Column(db.Float)
    finalTotalsPaid = db.Column(db.Float)

    # =====All Form 102 Employer =====
    companyName = db.Column(db.String(255))
    companyAddress = db.Column(db.String(255))
    taxFileNumber = db.Column(db.String(50))
    reportMonth = db.Column(db.Integer)
    reportYear = db.Column(db.Integer)

    # ===== Row 216 =====
    totalIncomeTax = db.Column(db.Float)
    totalGrossSalary = db.Column(db.Float)
    NumEmployees = db.Column(db.Integer)

    # ===== Row 254 =====
    totalPensionVal = db.Column(db.Float)
    totalCompVal = db.Column(db.Float)
    NumEmployeesNonSalary = db.Column(db.Integer)

    # ===== Row 291 =====
    totalEmpDeductions = db.Column(db.Float)
    totalContributions = db.Column(db.Float)

    # ===== Row 329 =====
    employerPension = db.Column(db.Float)
    totalPensionDeduction = db.Column(db.Float)
    NumEmployeesCharges = db.Column(db.Integer)

    # ===== Row 367 =====
    totalNationalInsurance = db.Column(db.Float)
    totalHealthInsurance = db.Column(db.Float)
    NumEmployeesCharges2 = db.Column(db.Integer)

    # ===== Row 404 =====
    finalTotalIncomeTax = db.Column(db.Float)

    # Frontend compatibility
    new_field_name = db.Column(db.String(50))
    value = db.Column(String(100))
    row_data = db.Column(db.JSON)
    role = db.Column(db.String, nullable=False)

    # Timesheet Task Total Hours
    task = db.Column(db.Text)
    totalHours = db.Column(db.Float)

    #  Timestamp for when this record was entered (optional but useful)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    submission_time = db.Column(db.DateTime, default=datetime.utcnow)

    #  Relationship to EmployeeHours
    hours_data = db.relationship('HoursData', back_populates='employee', lazy=True)
    monthly_records = db.relationship('MonthlyRecord', back_populates='employee', lazy=True)
    invoices = db.relationship('Invoice', back_populates='employee', lazy=True)
    timesheets = db.relationship('Timesheet', back_populates='employee', lazy=True)

    # Relationship to BankAccount model
    bank_account = db.relationship('BankAccount', backref='employee', uselist=False, lazy=True)

# -----------------------------
#  Bank Account  
# -----------------------------

class BankAccount(db.Model):
    __tablename__ = 'bank_account'

    id = db.Column(db.Integer, primary_key=True)
    bank_code = db.Column(db.String(10), nullable=False)
    branch_code = db.Column(db.String(10), nullable=False)
    account_number = db.Column(db.String(20), nullable=False)
    
    # Foreign key linking back to the EmployeeData model
    employee_id = db.Column(db.Integer, db.ForeignKey('employee_data.id'), unique=True, nullable=False)

    # Optional: For better security, you should encrypt sensitive data
    # encrypted_account_number = db.Column(db.String(256)) 

# -----------------------------
#  Invoice All  
# -----------------------------

class Invoice(db.Model):
    __tablename__ = 'invoice'

    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    invoice_date = db.Column(db.Date, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    allocation_number = db.Column(db.String(50), nullable=True)

    # Link to EmployeeData.id
    employee_id = db.Column(db.Integer, db.ForeignKey('employee_data.id'), nullable=False)

    # Relationship
    employee = db.relationship('EmployeeData', back_populates='invoices')

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

    def __repr__(self):
        return f'<Invoice #{self.invoice_number} for Employee ID: {self.employee_id}>'

# -----------------------------
#  Product All  
# -----------------------------

class Product(db.Model):
    __tablename__ = 'product'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255))
    
    def __repr__(self):
        return f'<Product {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'description': self.description
        }

# -----------------------------
#  Timesheets
# -----------------------------

class Timesheet(db.Model):
    __tablename__ = "timesheets"

    id = db.Column(db.Integer, primary_key=True)

    employee_id = db.Column(db.Integer, db.ForeignKey('employee_data.id'), nullable=False)

    employee_name = db.Column(db.String(100), nullable=False)
    isClockedIn = db.Column(db.String(5), nullable=False, default="false")

    id_number = db.Column(db.String(100))
    date = db.Column(db.String(32), nullable=False)
    startTime = db.Column(db.String(64), nullable=False)
    endTime = db.Column(db.String(64), nullable=False)
    startLocation = db.Column(db.Text)
    endLocation = db.Column(db.Text)
    task = db.Column(db.Text)
    totalHours = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    submission_time = db.Column(db.DateTime, default=datetime.utcnow)

    employee = db.relationship('EmployeeData', back_populates='timesheets')

# -----------------------------
#  Employee Hours All Hours Calculate
# -----------------------------

class HoursData(db.Model):
    __tablename__ = 'hours_data'

    id = db.Column(db.Integer, primary_key=True)
    #  Link to EmployeeData.id (internal system ID)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee_data.id'), nullable=False)

    employee_name = db.Column(db.String(100), nullable=False)
    employeeMonth = db.Column(db.String(2), nullable=False)
    employeeYear = db.Column(db.String(4), nullable=False)

    section = db.Column(db.String, nullable=True)   
    month_key = db.Column(db.String(7))  

    # --- Daily fields ---
    date_day = db.Column(db.String(10))
    date_block = db.Column(db.String(10))
    day = db.Column(db.String(10))
    saturday = db.Column(db.String(10))
    holiday = db.Column(db.String(10))
    start_time = db.Column(db.String(10))
    end_time = db.Column(db.String(10))
    hours_calculated = db.Column(db.String(10))
    hours_calculated_regular_day = db.Column(db.String(10))
    total_extra_hours_regular_day = db.Column(db.String(10))
    extra_hours125_regular_day = db.Column(db.String(10))
    extra_hours150_regular_day = db.Column(db.String(10))
    hours_holidays_day = db.Column(db.String(10))
    extra_hours150_holidays_saturday = db.Column(db.String(10))
    extra_hours175_holidays_saturday = db.Column(db.String(10))
    extra_hours200_holidays_saturday = db.Column(db.String(10))
    sick_day = db.Column(db.String(10))
    day_off = db.Column(db.String(10))
    food_break = db.Column(db.String(10))
    final_totals_hours = db.Column(db.String(10))
    calc1 = db.Column(db.String(10))
    calc2 = db.Column(db.String(10))
    calc3 = db.Column(db.String(10))
    work_day = db.Column(db.String(10))
    missing_work_day = db.Column(db.String(10))
    advance_payment = db.Column(db.String(10))

    # --- Monthly totals ---
    hours_calculated_monthly = db.Column(db.String(10))
    hours_calculated_regular_day_monthly = db.Column(db.String(10))
    total_extra_hours_regular_day_monthly = db.Column(db.String(10))
    extra_hours125_regular_day_monthly = db.Column(db.String(10))
    extra_hours150_regular_day_monthly = db.Column(db.String(10))
    hours_holidays_day_monthly = db.Column(db.String(10))
    extra_hours150_holidays_saturday_monthly = db.Column(db.String(10))
    extra_hours175_holidays_saturday_monthly = db.Column(db.String(10))
    extra_hours200_holidays_saturday_monthly = db.Column(db.String(10))
    sick_day_monthly = db.Column(db.String(10))
    day_off_monthly = db.Column(db.String(10))
    food_break_monthly = db.Column(db.String(10))
    final_totals_hours_monthly = db.Column(db.String(10))
    calc1_monthly = db.Column(db.String(10))
    calc2_monthly = db.Column(db.String(10))
    calc3_monthly = db.Column(db.String(10))
    work_day_monthly = db.Column(db.String(10))
    missing_work_day_monthly = db.Column(db.String(10))
    advance_payment_monthly = db.Column(db.String(10))

    # --- Paid totals ---
    hours_calculated_paid = db.Column(db.String(10))
    hours_calculated_regular_day_paid = db.Column(db.String(10))
    total_extra_hours_regular_day_paid = db.Column(db.String(10))
    extra_hours125_regular_day_paid = db.Column(db.String(10))
    extra_hours150_regular_day_paid = db.Column(db.String(10))
    hours_holidays_day_paid = db.Column(db.String(10))
    extra_hours150_holidays_saturday_paid = db.Column(db.String(10))
    extra_hours175_holidays_saturday_paid = db.Column(db.String(10))
    extra_hours200_holidays_saturday_paid = db.Column(db.String(10))
    sick_day_paid = db.Column(db.String(10))
    day_off_paid = db.Column(db.String(10))
    food_break_unpaid = db.Column(db.String(10))
    final_totals_hours_paid = db.Column(db.String(10))
    calc1_paid = db.Column(db.String(10))
    calc2_paid = db.Column(db.String(10))
    calc3_paid = db.Column(db.String(10))
    final_totals_lunch_value_paid = db.Column(db.String(10))  
    final_total_extra_hours_weekend_monthly = db.Column(db.String(10))
    advance_payment_paid = db.Column(db.String(10))

    # --- שעות מצטברות ---
    hours = db.Column(db.Float)
    date = db.Column(db.String(32))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    row_data = db.Column(db.JSON)

    # Explicit relationship back to EmployeeData
    employee = db.relationship('EmployeeData', back_populates='hours_data')

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

# -----------------------------
#  Monthly Record Form Data
# -----------------------------

class MonthlyRecord(db.Model):
    __tablename__ = 'monthly_records'

    id = db.Column(db.Integer, primary_key=True)

    #  Link to EmployeeData.id (internal system ID)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee_data.id'), nullable=False)

    employee_name = db.Column(db.String(100))
    employeeMonth = db.Column(db.String(2))       
    employeeYear = db.Column(db.String(4))        
    date = db.Column(db.String(10))                 
    month_result = db.Column(db.String(20))       
    save_date = db.Column(db.String(10))
    
    id_number = db.Column(db.String(100))  # Social security or identification number
    address = db.Column(db.String(100))
    city = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    phone = db.Column(db.String(20))
    mobile_value = db.Column(db.Float)
    clothing_value = db.Column(db.Float)
    cars_value = db.Column(db.Float)  
    email = db.Column(db.String(100))
    start_date = db.Column(db.String(10))                 
    date_of_birth = db.Column(db.String(10))                 
    monthly_city_tax_tops = db.Column(db.Float)
    bank_number = db.Column(db.String(20))
    branch_number = db.Column(db.String(20))
    account_number = db.Column(db.String(20))
    lunch_value = db.Column(db.Float)
    hourly_rate = db.Column(db.String(50))
    employee_number = db.Column(db.String(100))
    thirteenth_salary = db.Column(db.Float)
    message = db.Column(db.Text)
    work_apartment = db.Column(db.String(100))
    work_percent = db.Column(db.String(20))
    marital_status = db.Column(db.String(20))
    tax_credit_points = db.Column(db.String(20))
    hospital = db.Column(db.String(100))
    social_number = db.Column(db.String(20))
    irs_status = db.Column(db.String(20))
    contract_status = db.Column(db.String(20))
    tax_point_child = db.Column(db.String(20))

    # Tax and salary
    total_hours = db.Column(db.Float)
    basic_salary = db.Column(db.Float)
    additional_payments = db.Column(db.Float)
    net_value = db.Column(db.Float)
    gross_salary = db.Column(db.Float)
    above_ceiling_value = db.Column(db.Float)
    above_ceiling_fund = db.Column(db.Float)
    above_ceiling_compensation = db.Column(db.Float)
    gross_taxable = db.Column(db.Float)
    pension_fund = db.Column(db.Float)
    compensation = db.Column(db.Float)
    study_fund = db.Column(db.Float)
    disability = db.Column(db.Float)
    miscellaneous = db.Column(db.Float)
    national_insurance = db.Column(db.Float)
    total_employer_contributions = db.Column(db.Float)
    total_salary_cost = db.Column(db.Float)
    employee_pension_fund = db.Column(db.Float)
    self_employed_pension_fund = db.Column(db.Float)
    study_fund_deductions = db.Column(db.Float)
    miscellaneous_deductions = db.Column(db.Float)
    national_insurance_deductions = db.Column(db.Float)
    health_insurance_deductions = db.Column(db.Float)
    income_tax = db.Column(db.Float)
    total_deductions = db.Column(db.Float)
    net_payment = db.Column(db.Float)

    advance_payment_salary = db.Column(db.Float)

    #  Car-related fields
    car_value = db.Column(db.Float)  
    car_year = db.Column(db.String(10))  
    car_model = db.Column(db.String(50))  
    car_type = db.Column(db.String(50)) 

    #  City-related fields
    monthly_city_top_tax = db.Column(db.Float)  
    city_name = db.Column(db.String(100))  
    city_sign = db.Column(db.String(10))  
    city_value_percentage = db.Column(db.Float)  

    salary_tax = db.Column(db.Float)
    income_tax_before_credit = db.Column(db.Float, default=0.0)
    tax_level_precente = db.Column(db.Float, default=0.0)
    amount_tax_credit_points_monthly = db.Column(db.Float, default=0.0)
    total_salary_pension_funds = db.Column(db.Float, default=0.0)
    hours_table_data = db.Column(db.Text, nullable=True)
    total_work_days = db.Column(db.Float, default=0.0)
    totals_lunch_value = db.Column(db.Float, default=0.0)
    total_missing_hours = db.Column(db.Float, default=0.0)
    final_extra_hours_weekend = Column(Float, default=0.0)
    final_extra_hours_regular = Column(Float, default=0.0)
    food_break_unpaid_salary = Column(Float, default=0.0)

    hours125_regular_salary = Column(Float, default=0.0)
    hours150_regular_salary = Column(Float, default=0.0)
    hours150_holidays_saturday_salary = Column(Float, default=0.0)
    hours175_holidays_saturday_salary = Column(Float, default=0.0)
    hours200_holidays_saturday_salary = Column(Float, default=0.0)

    # Yearly Sick Days Vacation Fields
    sick_days_salary = db.Column(db.Float, default=0.0)
    vacation_days_salary = db.Column(db.Float, default=0.0)
    sick_days_salary_yearly = db.Column(db.Float, default=0.0)
    vacation_days_salary_yearly = db.Column(db.Float, default=0.0)
    sick_days_entitlement = db.Column(db.Float, default=0.0)
    vacation_days_entitlement = db.Column(db.Float, default=0.0)
    sick_days_balance_yearly = db.Column(db.Float, default=0.0)
    vacation_balance_yearly = db.Column(db.Float, default=0.0)
    gross_taxable_yearly = db.Column(db.Float, default=0.0)

    # Yearly Deduction Fields
    employee_pension_fund_yearly = db.Column(db.Float, default=0.0)
    self_employed_pension_fund_yearly = db.Column(db.Float, default=0.0)
    study_fund_deductions_yearly = db.Column(db.Float, default=0.0)
    miscellaneous_deductions_yearly = db.Column(db.Float, default=0.0)
    national_insurance_deductions_yearly = db.Column(db.Float, default=0.0)
    health_insurance_deductions_yearly = db.Column(db.Float, default=0.0)
    income_tax_yearly = db.Column(db.Float, default=0.0)
    amount_tax_credit_points_monthly_yearly = db.Column(db.Float, default=0.0)
    final_city_tax_benefit_yearly = db.Column(db.Float, default=0.0)

    # Yearly Employer Contribution Fields
    pension_fund_yearly = db.Column(db.Float, default=0.0)
    compensation_yearly = db.Column(db.Float, default=0.0)
    study_fund_yearly = db.Column(db.Float, default=0.0)
    disability_yearly = db.Column(db.Float, default=0.0)
    miscellaneous_yearly = db.Column(db.Float, default=0.0)
    national_insurance_yearly = db.Column(db.Float, default=0.0)
    salary_tax_yearly = db.Column(db.Float, default=0.0)
    total_employer_contributions_yearly = db.Column(db.Float, default=0.0)
    total_salary_cost_yearly = db.Column(db.Float, default=0.0)

    # Form 102 Monthly Fields
    employee_count = Column(Integer, default=0)
    total_gross = Column(Float, default=0.0)
    total_income_tax = Column(Float, default=0.0)
    total_ni_employee = Column(Float, default=0.0)
    total_health = Column(Float, default=0.0)
    total_study_fund_deductions = Column(Float, default=0.0)
    emp_pension = Column(Float, default=0.0)
    self_pension = Column(Float, default=0.0)
    final_emp_pension_combined = Column(Float, default=0.0)
    pension_val = Column(Float, default=0.0)
    comp_val = Column(Float, default=0.0)
    disability_val = Column(Float, default=0.0)
    total_employer_pension_combined = Column(Float, default=0.0)
    study_fund_val = Column(Integer, default=0)
    national_insurance_val = Column(Integer, default=0)
    final_emp_deductions_total = Column(Float, default=0.0)
    final_totals_income_tax = Column(Float, default=0.0)

    # Form B102 Monthly Fields
    regular_salary = db.Column(db.Float)
    reduced_salary = db.Column(db.Float)
    regular_count = db.Column(db.Integer)
    reduced_count = db.Column(db.Integer)
    total_salary = db.Column(db.Float)

    # Form 102 Monthly Fields
    eilat_regular_tax = db.Column(db.Float)
    eilat_benefit_20 = db.Column(db.Float)
    eilat_total_tax_after_benefit = db.Column(db.Float)
    controlling_salary = db.Column(db.Float)
    controlling_tax = db.Column(db.Float)
    outside_eilat_salary = db.Column(db.Float)
    outside_eilat_tax = db.Column(db.Float)
    total_tax_all = db.Column(db.Float)

    regularSalary = db.Column(db.Float)
    eilatRegularTax = db.Column(db.Float)
    eilatBenefit20 = db.Column(db.Float)
    eilatTotalTaxAfterBenefit = db.Column(db.Float)
    controllingSalary = db.Column(db.Float)
    controllingTax = db.Column(db.Float)
    outsideEilatSalary = db.Column(db.Float)
    outsideEilatTax = db.Column(db.Float)
    totalTaxAll = db.Column(db.Float)

    totalDisabilityVal = db.Column(db.Float)
    totalStudyFundVal = db.Column(db.Float)
    totalProvidentDeduction = db.Column(db.Float)
    totalEmpPension = db.Column(db.Float)
    totalSelfPension = db.Column(db.Float)
    finalTotalsPaid = db.Column(db.Float)

    # =====All Form 102 Employer =====
    companyName = db.Column(db.String(255))
    companyAddress = db.Column(db.String(255))
    taxFileNumber = db.Column(db.String(50))
    reportMonth = db.Column(db.Integer)
    reportYear = db.Column(db.Integer)

    # ===== Row 216 =====
    totalIncomeTax = db.Column(db.Float)
    totalGrossSalary = db.Column(db.Float)
    NumEmployees = db.Column(db.Integer)

    # ===== Row 254 =====
    totalPensionVal = db.Column(db.Float)
    totalCompVal = db.Column(db.Float)
    NumEmployeesNonSalary = db.Column(db.Integer)

    # ===== Row 291 =====
    totalEmpDeductions = db.Column(db.Float)
    totalContributions = db.Column(db.Float)

    # ===== Row 329 =====
    employerPension = db.Column(db.Float)
    totalPensionDeduction = db.Column(db.Float)
    NumEmployeesCharges = db.Column(db.Integer)

    # ===== Row 367 =====
    totalNationalInsurance = db.Column(db.Float)
    totalHealthInsurance = db.Column(db.Float)
    NumEmployeesCharges2 = db.Column(db.Integer)

    # ===== Row 404 =====
    finalTotalIncomeTax = db.Column(db.Float)

    # Frontend compatibility
    new_field_name = db.Column(db.String(50))
    value = db.Column(String(100))
    row_data = db.Column(db.JSON)
    role = db.Column(db.String(50))

    # Timesheet Task Total Hours
    task = db.Column(db.Text)
    totalHours = db.Column(db.Float)

    #  Timestamp for when this record was entered (optional but useful)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    submission_time = db.Column(db.DateTime, default=datetime.utcnow)

    #  Back-reference from EmployeeData
    employee = db.relationship('EmployeeData', back_populates='monthly_records')

    __table_args__ = (
        db.UniqueConstraint('employee_id', 'employeeMonth', 'employeeYear', name='unique_employee_month'),
    )

# -----------------------------
#  Customer Form Data
# -----------------------------
class CustomerForm(db.Model):
    __tablename__ = 'customer_forms' 
    
    id = db.Column(db.Integer, primary_key=True) 
    date = db.Column(db.String(10))
    customer_name = db.Column(db.String(100))
    id_number = db.Column(db.String(100))
    address = db.Column(db.String(100))
    city = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    phone = db.Column(db.String(20))
    clothing_value = db.Column(db.Float)
    car_value = db.Column(db.Float)
    email = db.Column(db.String(100))
    start_date = db.Column(db.String(10))
    bank_number = db.Column(db.String(20))
    branch_number = db.Column(db.String(20))
    account_number = db.Column(db.String(20))
    lunch_value = db.Column(db.Float)
    mobile_value = db.Column(db.Float)
    hourly_rate = db.Column(db.Float)
    customer_number = db.Column(db.String(100))
    thirteenth_salary = db.Column(db.Float)
    message = db.Column(db.Text)
    work_apartment = db.Column(db.String(100))
    work_percent = db.Column(db.String(20))
    marital_status = db.Column(db.String(20))
    tax_point = db.Column(db.String(20))
    hospital = db.Column(db.String(100))
    social_number = db.Column(db.String(20))
    irs_status = db.Column(db.String(20))
    contract_status = db.Column(db.String(20))
    tax_point_child = db.Column(db.String(20))

# -----------------------------
#  Tax Credit Data
# -----------------------------
class TaxCredit(db.Model):
    __tablename__ = 'tax_credits'

    id = db.Column(db.Integer, primary_key=True)
    is_israeli_resident = db.Column(db.Boolean, nullable=False)
    gender = db.Column(db.String(10), nullable=False) 
    is_teenager = db.Column(db.Boolean, nullable=False)
    is_married = db.Column(db.Boolean, nullable=False)
    is_special_situation = db.Column(db.Boolean, nullable=False)
    has_children = db.Column(db.Boolean, nullable=False)
    married_to_widower = db.Column(db.Boolean, nullable=False)
    single_parent = db.Column(db.Boolean, nullable=False)
    separate_household = db.Column(db.Boolean, nullable=False)
    single_parent_no_spouse = db.Column(db.Boolean, nullable=False)
    paying_child_support = db.Column(db.Boolean, nullable=False)
    remarried_paying_alimony = db.Column(db.Boolean, nullable=False)
    newborn_count = db.Column(db.Integer, nullable=False)
    age_1_count = db.Column(db.Integer, nullable=False)
    age_2_count = db.Column(db.Integer, nullable=False)
    age_3_count = db.Column(db.Integer, nullable=False)
    age_4_count = db.Column(db.Integer, nullable=False)
    age_5_count = db.Column(db.Integer, nullable=False)
    age_6_17_count = db.Column(db.Integer, nullable=False)
    age_18_count = db.Column(db.Integer, nullable=False)
    children_not_in_custody = db.Column(db.Integer, nullable=False)
    total_tax_credits = db.Column(db.Float, nullable=False)
    
    pass
    
