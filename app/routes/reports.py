from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import SaleTransaction, SaleItem, Medication, Customer
from app.utils.helpers import get_sales_report, get_daily_sales_chart_data, get_sales_summary
from datetime import datetime, timedelta
import pandas as pd
from io import BytesIO

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/')
@login_required
def reports():
    return render_template('reports/reports.html')

@reports_bp.route('/sales')
@login_required
def sales_reports():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            sales = get_sales_report(start_date, end_date)
        except ValueError:
            flash('Invalid date format', 'danger')
            sales = []
    else:
        # Default to current month
        current_month = datetime.now().strftime('%Y-%m')
        sales = get_sales_report()
    
    # Calculate totals
    total_sales = sum(sale.total_amount for sale in sales)
    total_transactions = len(sales)
    
    return render_template('reports/sales_reports.html', 
                         sales=sales, 
                         total_sales=total_sales, 
                         total_transactions=total_transactions,
                         start_date=start_date,
                         end_date=end_date)

@reports_bp.route('/export/sales')
@login_required
def export_sales_report():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            sales = get_sales_report(start_date, end_date)
        except ValueError:
            flash('Invalid date format', 'danger')
            return redirect(url_for('reports.sales_reports'))
    else:
        sales = get_sales_report()
    
    # Create DataFrame
    data = []
    for sale in sales:
        data.append({
            'Transaction ID': sale.transaction_id,
            'Date': sale.sale_date.strftime('%Y-%m-%d %H:%M'),
            'Customer': sale.customer.name if sale.customer else 'Walk-in',
            'Total Amount': float(sale.total_amount),
            'Tax': float(sale.tax_amount),
            'Discount': float(sale.discount_amount),
            'Payment Method': sale.payment_method,
            'Cashier': sale.user.username
        })
    
    df = pd.DataFrame(data)
    
    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Sales Report', index=False)
    
    output.seek(0)
    
    filename = f'sales_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    return send_file(output, as_attachment=True, download_name=filename)

@reports_bp.route('/inventory')
@login_required
def inventory_reports():
    filter_type = request.args.get('filter', 'all')
    
    if filter_type == 'low_stock':
        medications = get_low_stock_medications()
    elif filter_type == 'expired':
        medications = get_expired_medications()
    elif filter_type == 'expiring_soon':
        medications = get_expiring_soon_medications()
    else:
        medications = get_all_medications()
    
    return render_template('reports/inventory_reports.html', 
                         medications=medications, 
                         filter_type=filter_type,
                         now=datetime.now().date())

@reports_bp.route('/export/inventory')
@login_required
def export_inventory_report():
    filter_type = request.args.get('filter', 'all')
    
    if filter_type == 'low_stock':
        medications = get_low_stock_medications()
    elif filter_type == 'expired':
        medications = get_expired_medications()
    elif filter_type == 'expiring_soon':
        medications = get_expiring_soon_medications()
    else:
        medications = get_all_medications()
    
    # Create DataFrame
    data = []
    for med in medications:
        data.append({
            'Name': med.name,
            'Generic Name': med.generic_name,
            'Manufacturer': med.manufacturer,
            'Price': float(med.price),
            'Cost Price': float(med.cost_price) if med.cost_price else 0,
            'Stock Quantity': med.stock_quantity,
            'Expiry Date': med.expiry_date.strftime('%Y-%m-%d') if med.expiry_date else 'N/A',
            'Category': med.category,
            'Barcode': med.barcode
        })
    
    df = pd.DataFrame(data)
    
    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Inventory Report', index=False)
    
    output.seek(0)
    
    filename = f'inventory_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    return send_file(output, as_attachment=True, download_name=filename)

@reports_bp.route('/profit')
@login_required
def profit_reports():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            profit_data = get_profit_report(start_date, end_date)
        except ValueError:
            flash('Invalid date format', 'danger')
            profit_data = {'sales': [], 'total_profit': 0, 'total_revenue': 0}
    else:
        # Default to current month
        current_month = datetime.now().strftime('%Y-%m')
        profit_data = get_profit_report()
    
    return render_template('reports/profit_reports.html', 
                         sales=profit_data['sales'], 
                         total_profit=profit_data['total_profit'],
                         total_revenue=profit_data['total_revenue'],
                         start_date=start_date,
                         end_date=end_date)

@reports_bp.route('/export/profit')
@login_required
def export_profit_report():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            profit_data = get_profit_report(start_date, end_date)
        except ValueError:
            flash('Invalid date format', 'danger')
            return redirect(url_for('reports.profit_reports'))
    else:
        profit_data = get_profit_report()
    
    # Create DataFrame
    data = []
    for sale in profit_data['sales']:
        data.append({
            'Transaction ID': sale.transaction_id,
            'Date': sale.sale_date.strftime('%Y-%m-%d %H:%M'),
            'Customer': sale.customer.name if sale.customer else 'Walk-in',
            'Total Revenue': float(sale.total_amount),
            'Total Profit': float(get_sale_profit(sale.id)),
            'Payment Method': sale.payment_method,
            'Cashier': sale.user.username
        })
    
    df = pd.DataFrame(data)
    
    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Profit Report', index=False)
    
    output.seek(0)
    
    filename = f'profit_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    return send_file(output, as_attachment=True, download_name=filename)

@reports_bp.route('/api/sales/chart')
@login_required
def api_sales_chart():
    days = int(request.args.get('days', 30))
    chart_data = get_daily_sales_chart_data(days)
    return jsonify(chart_data)

@reports_bp.route('/api/sales_summary')
@login_required
def api_sales_summary():
    stats = get_sales_summary()
    return jsonify(stats)

@reports_bp.route('/customer')
@login_required
def customer_reports():
    customers = Customer.query.order_by(Customer.name).all()
    
    # Calculate sales data for each customer
    customer_data = []
    for customer in customers:
        sales_count = len(customer.sales)
        total_spent = sum(sale.total_amount for sale in customer.sales)
        customer_data.append({
            'customer': customer,
            'sales_count': sales_count,
            'total_spent': total_spent
        })
    
    # Sort by total spent descending
    customer_data.sort(key=lambda x: x['total_spent'], reverse=True)
    
    return render_template('reports/customer_reports.html', customer_data=customer_data)

@reports_bp.route('/export/customer')
@login_required
def export_customer_report():
    customers = Customer.query.order_by(Customer.name).all()
    
    # Create DataFrame
    data = []
    for customer in customers:
        sales_count = len(customer.sales)
        total_spent = sum(sale.total_amount for sale in customer.sales)
        data.append({
            'Customer Name': customer.name,
            'Phone': customer.phone or 'N/A',
            'Email': customer.email or 'N/A',
            'Total Purchases': sales_count,
            'Total Spent': float(total_spent),
            'Average Purchase': float(total_spent / sales_count) if sales_count > 0 else 0
        })
    
    df = pd.DataFrame(data)
    
    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Customer Report', index=False)
    
    output.seek(0)
    
    filename = f'customer_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    return send_file(output, as_attachment=True, download_name=filename)

# Helper functions
def get_low_stock_medications(threshold=10):
    from sqlalchemy import and_
    return Medication.query.filter(
        and_(
            Medication.stock_quantity <= threshold,
            Medication.deleted == False
        )
    ).all()

def get_expired_medications():
    from sqlalchemy import and_
    today = datetime.now().date()
    return Medication.query.filter(
        and_(
            Medication.expiry_date.isnot(None),
            Medication.expiry_date < today,
            Medication.deleted == False
        )
    ).all()

def get_expiring_soon_medications(days=30):
    from sqlalchemy import and_
    today = datetime.now().date()
    soon_date = today + timedelta(days=days)
    return Medication.query.filter(
        and_(
            Medication.expiry_date.isnot(None),
            Medication.expiry_date >= today,
            Medication.expiry_date <= soon_date,
            Medication.deleted == False
        )
    ).all()

def get_all_medications():
    return Medication.query.filter_by(deleted=False).order_by(Medication.name).all()

def get_profit_report(start_date=None, end_date=None):
    from sqlalchemy.orm import joinedload
    query = SaleTransaction.query.options(
        joinedload(SaleTransaction.customer),
        joinedload(SaleTransaction.user)
    ).filter(SaleTransaction.payment_status == 'completed')
    
    if start_date and end_date:
        query = query.filter(SaleTransaction.sale_date.between(start_date, end_date))
    elif start_date:
        query = query.filter(SaleTransaction.sale_date >= start_date)
    elif end_date:
        query = query.filter(SaleTransaction.sale_date <= end_date)
    
    sales = query.order_by(SaleTransaction.sale_date.desc()).all()
    
    total_profit = 0
    total_revenue = 0
    
    for sale in sales:
        sale_profit = get_sale_profit(sale.id)
        total_profit += sale_profit
        total_revenue += float(sale.total_amount)
    
    return {
        'sales': sales,
        'total_profit': total_profit,
        'total_revenue': total_revenue
    }

def get_sale_profit(sale_id):
    from sqlalchemy import func
    profit = db.session.query(
        func.coalesce(func.sum(SaleItem.quantity * (SaleItem.unit_price - Medication.cost_price)), 0)
    ).join(Medication, SaleItem.medication_id == Medication.id
    ).filter(SaleItem.sale_id == sale_id).scalar()
    
    return float(profit) if profit else 0