from flask_sqlalchemy import SQLAlchemy
from database import db, EmployeeData, MonthlyRecord, HoursData, PasswordResetToken, CustomerForm, TaxCredit, BankAccount , Invoice , Product, Timesheet, User

# In-Memory Storage for Employees
employees = []

def get_employees():
    """Returns the list of employees."""
    return employees

def add_employee(employee_data):
    """Adds a new employee to the list."""
    employees.append(employee_data)


# In-Memory Storage for Customers
customers = []

def get_customers():
    """Returns the list of customers."""
    return customers

def add_customer(customer_data):
    """Adds a new customer to the list."""
    customers.append(customer_data)

# In-Memory Storage for Tax Credits
tax_credits = []

def get_tax_credits():
    """Returns the list of tax credits."""
    return tax_credits

def add_tax_credit(tax_credit_data):
    """Adds a new tax credit to the list."""
    tax_credits.append(tax_credit_data)
