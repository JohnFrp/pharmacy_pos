from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user
from app.utils.helpers import get_sales_summary, get_daily_sales_chart_data
from datetime import datetime, timedelta
from app.models import SaleTransaction, Medication, User

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        # User is logged in - show dashboard
        stats = get_sales_summary()
        
        # Get additional stats for dashboard
        from app.utils.helpers import get_expiring_soon_medications
        expiring_soon_count = len(get_expiring_soon_medications())
        
        # Get recent activity counts
        recent_sales_count = SaleTransaction.query.filter(
            SaleTransaction.sale_date >= datetime.now() - timedelta(days=1)
        ).count()
        
        recent_medications_count = Medication.query.filter(
            Medication.created_at >= datetime.now() - timedelta(days=7)
        ).count()
        
        total_users_count = User.query.count()
        
        # Get chart data
        chart_data = get_daily_sales_chart_data(7)
        
        return render_template('index.html', 
                             stats=stats,
                             expiring_soon_count=expiring_soon_count,
                             recent_sales_count=recent_sales_count,
                             recent_medications_count=recent_medications_count,
                             total_users_count=total_users_count,
                             chart_data=chart_data)
    else:
        # User is not logged in - base.html will show welcome page
        return render_template('index.html')

@main_bp.route('/search')
def search():
    from flask import request
    from app.utils.helpers import search_medications
    
    search_term = request.args.get('q', '')
    results = []
    if search_term:
        results = search_medications(search_term)
    return render_template('search.html', results=results, search_term=search_term)