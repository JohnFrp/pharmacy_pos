from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from app import db
from app.models import User, Medication, SaleTransaction, SaleItem, Customer

def create_admin_user():
    """Create admin user if it doesn't exist"""
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        try:
            admin_user = User(
                username='admin',
                email='admin@pharmacy.com',
                role='admin',
                is_approved=True,
                is_active=True
            )
            admin_user.set_password('admin123')
            
            db.session.add(admin_user)
            db.session.commit()
            print("✅ Admin user created: username='admin', password='admin123'")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating admin user: {str(e)}")

def get_sales_summary():
    # Total medications (exclude deleted)
    total_medications = Medication.query.filter_by(deleted=False).count()
    
    # Low stock count (exclude deleted)
    low_stock_count = Medication.query.filter(
        and_(
            Medication.stock_quantity <= 10,
            Medication.deleted == False
        )
    ).count()
    
    # Expired medications count (exclude deleted)
    expired_count = Medication.query.filter(
        and_(
            Medication.expiry_date.isnot(None),
            Medication.expiry_date < datetime.now().date(),
            Medication.deleted == False
        )
    ).count()
    
    # Today's sales
    today = datetime.now().date()
    today_sales = db.session.query(
        func.coalesce(func.sum(SaleTransaction.total_amount), 0)
    ).filter(
        func.date(SaleTransaction.sale_date) == today,
        SaleTransaction.payment_status == 'completed'
    ).scalar()
    
    # Month sales
    current_month = datetime.now().strftime('%Y-%m')
    month_sales = db.session.query(
        func.coalesce(func.sum(SaleTransaction.total_amount), 0)
    ).filter(
        func.to_char(SaleTransaction.sale_date, 'YYYY-MM') == current_month,
        SaleTransaction.payment_status == 'completed'
    ).scalar()
    
    # Today's profit
    today_profit = db.session.query(
        func.coalesce(func.sum(SaleItem.quantity * (SaleItem.unit_price - Medication.cost_price)), 0)
    ).join(Medication, SaleItem.medication_id == Medication.id
    ).join(SaleTransaction, SaleItem.sale_id == SaleTransaction.id
    ).filter(
        func.date(SaleTransaction.sale_date) == today,
        SaleTransaction.payment_status == 'completed'
    ).scalar()
    
    return {
        'total_medications': total_medications,
        'low_stock_count': low_stock_count,
        'expired_count': expired_count,
        'today_sales': float(today_sales),
        'month_sales': float(month_sales),
        'today_profit': float(today_profit) if today_profit else 0
    }

# Add other helper functions from your original code here...
# search_medications, get_low_stock_medications, get_expired_medications, etc.