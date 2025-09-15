from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Medication, SaleTransaction, SaleItem, Customer
from app.utils.helpers import process_sale_transaction, get_sale_details, get_filtered_sales
from datetime import datetime
import json

sales_bp = Blueprint('sales', __name__)

@sales_bp.route('/', methods=['GET', 'POST'])
@login_required
def sales():
    if request.method == 'POST':
        try:
            # Log the raw request data for debugging
            print("Raw request data:", request.data)
            print("Request form:", request.form)
            
            # Check if data is JSON (from AJAX) or form data
            if request.is_json:
                data = request.get_json()
                print("JSON data received:", data)
                items = data.get('items', [])
                customer_id = data.get('customer_id')
                payment_method = data.get('payment_method', 'cash')
                discount = float(data.get('discount', 0))
                tax_rate = float(data.get('tax_rate', 0))
                notes = data.get('notes', '')
            else:
                # Fallback to form data
                items_data = request.form.get('items', '[]')
                print("Form items data:", items_data)
                items = json.loads(items_data)
                customer_id = request.form.get('customer_id')
                payment_method = request.form.get('payment_method', 'cash')
                discount = float(request.form.get('discount', 0))
                tax_rate = float(request.form.get('tax_rate', 0))
                notes = request.form.get('notes', '')
            
            print("Parsed items:", items)
            
            # Validate items
            if not items or len(items) == 0:
                error_msg = 'No items in cart. Please add medications to complete sale.'
                if request.is_json:
                    return jsonify({
                        'success': False,
                        'error': error_msg
                    }), 400
                else:
                    flash(error_msg, 'warning')
                    return redirect(url_for('sales.sales'))
            
            # Validate each item
            for i, item in enumerate(items):
                print(f"Validating item {i}:", item)
                
                if 'medication_id' not in item:
                    error_msg = f'Item {i+1} is missing medication_id. Item data: {item}'
                    if request.is_json:
                        return jsonify({
                            'success': False,
                            'error': error_msg
                        }), 400
                    else:
                        flash(error_msg, 'danger')
                        return redirect(url_for('sales.sales'))
                
                if 'unit_price' not in item:
                    error_msg = f'Item {i+1} is missing unit_price'
                    if request.is_json:
                        return jsonify({
                            'success': False,
                            'error': error_msg
                        }), 400
                    else:
                        flash(error_msg, 'danger')
                        return redirect(url_for('sales.sales'))
                
                if 'quantity' not in item:
                    error_msg = f'Item {i+1} is missing quantity'
                    if request.is_json:
                        return jsonify({
                            'success': False,
                            'error': error_msg
                        }), 400
                    else:
                        flash(error_msg, 'danger')
                        return redirect(url_for('sales.sales'))
            
            # Convert customer_id to integer or None
            if customer_id and customer_id != 'new' and customer_id != 'null' and customer_id != '':
                try:
                    customer_id = int(customer_id)
                except ValueError:
                    customer_id = None
            else:
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
                    'message': f'Sale completed successfully! Transaction ID: {sale.transaction_id}',
                    'sale_id': sale.id
                })
            else:
                flash(f'Sale completed successfully! Transaction ID: {sale.transaction_id}', 'success')
                return redirect(url_for('sales.receipt', sale_id=sale.id))
            
        except Exception as e:
            error_msg = f'Error processing sale: {str(e)}'
            print("Error details:", error_msg)
            import traceback
            traceback.print_exc()
            
            if request.is_json:
                return jsonify({
                    'success': False,
                    'error': error_msg
                }), 400
            else:
                flash(error_msg, 'danger')
                return redirect(url_for('sales.sales'))
    
    medications = Medication.query.filter(Medication.stock_quantity > 0, Medication.deleted == False).order_by(Medication.name).all()
    customers = Customer.query.order_by(Customer.name).all()
    
    # Convert customers to a serializable format
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
    
    # Calculate statistics
    total_revenue = 0
    avg_transaction = 0
    today_revenue = 0
    
    if sales:
        # Calculate total revenue and average transaction
        total_revenue = sum(sale.total_amount for sale in sales)
        avg_transaction = total_revenue / len(sales)
    
    # Calculate today's revenue
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
    
    return render_template('sales/view_transaction.html', sale=sale)

@sales_bp.route('/api/customers/search')
@login_required
def api_customers_search():
    search_term = request.args.get('q', '')
    customers = Customer.query.filter(
        Customer.name.ilike(f'%{search_term}%') |
        Customer.phone.ilike(f'%{search_term}%') |
        Customer.email.ilike(f'%{search_term}%')
    ).order_by(Customer.name).all() if search_term else Customer.query.order_by(Customer.name).all()
    
    results = []
    for customer in customers:
        results.append({
            'id': customer.id,
            'name': customer.name,
            'phone': customer.phone,
            'email': customer.email
        })
    
    return jsonify(results)

@sales_bp.route('/api/customers/add', methods=['POST'])
@login_required
def api_customers_add():
    try:
        data = request.get_json()
        customer = Customer(
            name=data.get('name'),
            phone=data.get('phone'),
            email=data.get('email'),
            address=data.get('address')
        )
        
        db.session.add(customer)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'customer': {
                'id': customer.id,
                'name': customer.name,
                'phone': customer.phone,
                'email': customer.email
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@sales_bp.route('/debug/cart', methods=['POST'])
@login_required
def debug_cart():
    """Debug endpoint to check what's being sent from the frontend"""
    try:
        if request.is_json:
            data = request.get_json()
            return jsonify({
                'received': True,
                'data': data,
                'items_count': len(data.get('items', [])),
                'customer_id': data.get('customer_id'),
                'payment_method': data.get('payment_method')
            })
        else:
            return jsonify({
                'received': False,
                'error': 'No JSON data received'
            }), 400
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@sales_bp.route('/debug/medications')
@login_required
def debug_medications():
    """Debug endpoint to check medication data"""
    medications = Medication.query.filter_by(deleted=False).all()
    result = []
    for med in medications:
        result.append({
            'id': med.id,
            'name': med.name,
            'price': float(med.price),
            'stock': med.stock_quantity
        })
    return jsonify(result)