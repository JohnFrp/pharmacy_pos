from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    try:
        # Test database connection
        result = db.session.execute('SELECT 1').scalar()
        print("✅ Database connection successful!")
        
        # Test if tables exist
        users_count = User.query.count()
        print(f"✅ Users table exists with {users_count} records")
        
    except Exception as e:
        print(f"❌ Database error: {str(e)}")