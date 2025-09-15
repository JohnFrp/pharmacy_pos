import traceback
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Medication, SaleTransaction, SaleItem, Customer
from app.utils.helpers import process_sale_transaction, get_sale_details, get_filtered_sales
from datetime import datetime
import json

sales_bp = Blueprint('sales', __name__)

@sales_bp.route('/sales', methods=['GET', 'POST'])
@login_required
def sales():
    if request.method == 'POST':
        try:
            # REFACTOR: Consolidate data extraction from JSON or Form data
            if request.is_json:
                data = request.get_json()
            else:
                # Safely parse items from form, default to empty list on failure
                try:
                    items_data = request.form.get('items', '[]')
                    items = json.loads(items_data)
                except json.JSONDecodeError:
                    items = []
                data = {
                    'items': items,
                    'customer_id': request.form.get('customer_id'),
                    'payment_method': request.form.get('payment_method', 'cash'),
                    'discount': request.form.get('discount', '0'),
                    'tax_rate': request.form.get('tax_rate', '0'),
                    'notes': request.form.get('notes', '')
                }

            items = data.get('items', [])
            customer_id_raw = data.get('customer_id')
            payment_method = data.get('payment_method', 'cash')
            notes = data.get('notes', '')

            # FIX: Safely convert string values to float, defaulting to 0.0 on error
            try:
                discount = float(data.get('discount', 0))
                tax_rate = float(data.get('tax_rate', 0))
            except (ValueError, TypeError):
                discount = 0.0
                tax_rate = 0.0

            # Validate items
            if not items:
                error_msg = 'Your cart is empty. Please add items to proceed.'
                return jsonify({'success': False, 'error': error_msg}), 400 if request.is_json else (flash(error_msg, 'warning'), redirect(url_for('sales.sales')))

            # REFACTOR: Clean up customer_id parsing
            customer_id = None
            if customer_id_raw and str(customer_id_raw).lower() not in ['new', 'null', '']:
                try:
                    customer_id = int(customer_id_raw)
                except (ValueError, TypeError):
                    # BEST PRACTICE: Log this unexpected value for debugging
                    current_app.logger.warning(f"Invalid customer_id value received: {customer_id_raw}")
                    customer_id = None
            
            # Process the sale
            sale = process_sale_transaction(
                items=items,
                customer_id=customer_id,
                user_id=current_user.id,
                payment_method=payment_method,
                discount=discount,
                tax_rate=tax_rate,
                notes=notes
            )
            
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': f'Sale completed! Transaction ID: {sale.transaction_id}',
                    'sale_id': sale.id
                })
            else:
                flash(f'Sale completed! Transaction ID: {sale.transaction_id}', 'success')                
                return redirect(url_for('sales.view_receipt', sale_id=sale.id))

        except Exception as e:
            # BEST PRACTICE: Use logging instead of print for production
            current_app.logger.error(f'Error processing sale: {str(e)}')
            current_app.logger.error(traceback.format_exc())
            
            error_msg = 'An unexpected error occurred while processing the sale. Please try again.'
            
            if request.is_json:
                return jsonify({'success': False, 'error': error_msg}), 500
            else:
                flash(error_msg, 'danger')
                return redirect(url_for('sales.sales'))
    
    # GET request logic remains the same
    medications = Medication.query.filter(Medication.stock_quantity > 0, Medication.deleted == False).order_by(Medication.name).all()
    customers = Customer.query.order_by(Customer.name).all()
    customers_data = [customer.to_dict() for customer in customers]
    
    return render_template('sales/sales.html', medications=medications, customers=customers_data)

@sales_bp.route('/receipt/<int:sale_id>')
@login_required
def view_receipt(sale_id):
    sale = get_sale_details(sale_id)
    if not sale:
        flash('Sale not found', 'danger')
        return redirect(url_for('sales.transactions'))
    
    return render_template('sales/receipt.html', sale=sale)

@sales_bp.route('/receipt/print/<int:sale_id>')
@login_required
def print_receipt(sale_id):
    sale = get_sale_details(sale_id)
    if not sale:
        flash('Sale not found', 'danger')
        return redirect(url_for('sales.transactions'))
    
    return render_template('sales/print_receipt.html', sale=sale)

@sales_bp.route('/transactions')
@login_required
def transactions():
    filter_type = request.args.get('filter', 'all')
    sales = get_filtered_sales(filter_type)
    
    total_revenue = 0
    avg_transaction = 0
    today_revenue = 0
    
    if sales:
        total_revenue = sum(sale.total_amount for sale in sales)
        # FIX: Prevent ZeroDivisionError if there are no sales
        if len(sales) > 0:
            avg_transaction = total_revenue / len(sales)
    
    today_sales = get_filtered_sales('today')
    if today_sales:
        today_revenue = sum(sale.total_amount for sale in today_sales)
    
    return render_template('sales/transactions.html', 
                           sales=sales, 
                           filter_type=filter_type,
                           total_revenue=total_revenue,
                           avg_transaction=avg_transaction,
                           today_revenue=today_revenue)

@sales_bp.route('/transaction/<int:sale_id>')
@login_required
def view_transaction(sale_id):
    sale = get_sale_details(sale_id)
    if not sale:
        flash('Transaction not found', 'danger')
        return redirect(url_for('sales.transactions'))
    
    return render_template('sales/transaction.html', sale=sale)



@sales_bp.route('/api/customers/search')
@login_required
def api_customers_search():
    search_term = request.args.get('q', '').strip()
    query = Customer.query
    if search_term:
        search_filter = f'%{search_term}%'
        query = query.filter(
            Customer.name.ilike(search_filter) |
            Customer.phone.ilike(search_filter) |
            Customer.email.ilike(search_filter)
        )
    
    customers = query.order_by(Customer.name).all()
    return jsonify([customer.to_dict() for customer in customers])

@sales_bp.route('/api/customers/add', methods=['POST'])
@login_required
def api_customers_add():
    try:
        data = request.get_json()
        if not data or not data.get('name'):
            return jsonify({'success': False, 'error': 'Customer name is required.'}), 400

        customer = Customer(
            name=data.get('name'),
            phone=data.get('phone'),
            email=data.get('email'),
            address=data.get('address')
        )
        
        db.session.add(customer)
        db.session.commit()
        
        return jsonify({'success': True, 'customer': customer.to_dict()})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding customer: {str(e)}")
        return jsonify({'success': False, 'error': 'Could not add new customer.'}), 500

# Your debug routes can remain as they are for development purposes.
# ... (debug_cart and debug_medications)