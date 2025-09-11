from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
from app import db
from app.models import Customer

customers_bp = Blueprint('customers', __name__)

@customers_bp.route('/')
@login_required
def customers():
    search_term = request.args.get('q', '')
    if search_term:
        customers = search_customers(search_term)
    else:
        customers = Customer.query.order_by(Customer.name).all()
    
    return render_template('customers/customers.html', customers=customers, search_term=search_term)

@customers_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_customer():
    if request.method == 'POST':
        try:
            name = request.form['name']
            phone = request.form.get('phone', '')
            email = request.form.get('email', '')
            address = request.form.get('address', '')
            
            customer = Customer(name=name, phone=phone, email=email, address=address)
            db.session.add(customer)
            db.session.commit()
            
            flash('Customer added successfully!', 'success')
            return redirect(url_for('customers.customers'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding customer: {str(e)}', 'danger')
    
    return render_template('customers/add_customer.html')

@customers_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_customer(id):
    customer = Customer.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            customer.name = request.form['name']
            customer.phone = request.form.get('phone', '')
            customer.email = request.form.get('email', '')
            customer.address = request.form.get('address', '')
            
            db.session.commit()
            
            flash('Customer updated successfully!', 'success')
            return redirect(url_for('customers.customers'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating customer: {str(e)}', 'danger')
    
    return render_template('customers/edit_customer.html', customer=customer)

@customers_bp.route('/delete/<int:id>')
@login_required
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    
    try:
        # Check if customer has any sales
        if customer.sales:
            flash('Cannot delete customer with existing sales records.', 'danger')
            return redirect(url_for('customers.customers'))
        
        db.session.delete(customer)
        db.session.commit()
        flash('Customer deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting customer: {str(e)}', 'danger')
    
    return redirect(url_for('customers.customers'))

@customers_bp.route('/view/<int:id>')
@login_required
def view_customer(id):
    customer = Customer.query.get_or_404(id)
    return render_template('customers/view_customer.html', customer=customer)

@customers_bp.route('/api/search')
@login_required
def api_customers_search():
    search_term = request.args.get('q', '')
    customers = search_customers(search_term) if search_term else Customer.query.order_by(Customer.name).all()
    
    results = []
    for customer in customers:
        results.append({
            'id': customer.id,
            'name': customer.name,
            'phone': customer.phone,
            'email': customer.email,
            'address': customer.address
        })
    
    return results

# Helper functions
def search_customers(search_term):
    search_pattern = f'%{search_term}%'
    return Customer.query.filter(
        Customer.name.ilike(search_pattern) |
        Customer.phone.ilike(search_pattern) |
        Customer.email.ilike(search_pattern)
    ).all()

def get_customer_by_id(customer_id):
    return Customer.query.get(customer_id)

def create_customer(name, phone=None, email=None, address=None):
    customer = Customer(name=name, phone=phone, email=email, address=address)
    db.session.add(customer)
    db.session.commit()
    return customer