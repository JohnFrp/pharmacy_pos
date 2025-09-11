from app import create_app, db
from app.models import User
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Test database connection with proper text() wrapper
        result = db.session.execute(text('SELECT 1')).scalar()
        print("✅ Database connection successful!")
        
        # Test if tables exist
        users_count = db.session.execute(text('SELECT COUNT(*) FROM users')).scalar()
        print(f"✅ Users table exists with {users_count} records")
        
        # Test if we can query medications
        meds_count = db.session.execute(text('SELECT COUNT(*) FROM medications')).scalar()
        print(f"✅ Medications table exists with {meds_count} records")
        
        # Test if admin user exists
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            print("✅ Admin user exists")
        else:
            print("⚠️ Admin user not found")
            
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        import traceback
        traceback.print_exc()