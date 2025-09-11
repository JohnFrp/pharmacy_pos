from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, send_file
from flask_login import login_required, current_user
from app import db
from app.models import User, Medication, SaleTransaction, SaleItem, Customer
from app.utils.decorators import admin_required
from app.utils.helpers import get_sales_summary
import json
from sqlalchemy import text, inspect
from datetime import datetime
from io import BytesIO
import pandas as pd

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
@login_required
@admin_required
def admin_panel():
    # Get statistics for admin dashboard
    user_count = User.query.count()
    admin_count = User.query.filter_by(role='admin').count()
    sales_count = SaleTransaction.query.count()
    
    stats = {
        'user_count': user_count,
        'admin_count': admin_count,
        'sales_count': sales_count,
        **get_sales_summary()  # Include the existing sales stats
    }
    
    return render_template('admin/admin_panel.html', stats=stats)

# Add other admin routes here...
# admin_users, admin_pending_approvals, admin_approve_user, etc.