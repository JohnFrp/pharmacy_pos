from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    try:
        # Test user loader
        from flask_login import LoginManager
        login_manager = LoginManager()
        login_manager.init_app(app)
        
        # Test creating a user
        test_user = User(
            username='testuser',
            email='test@example.com',
            role='user',
            is_active=True,
            is_approved=True
        )
        test_user.set_password('testpassword')
        
        db.session.add(test_user)
        db.session.commit()
        print("✅ Test user created successfully")
        
        # Test user loader
        @login_manager.user_loader
        def load_user(user_id):
            try:
                return User.query.get(int(user_id))
            except:
                return None
        
        loaded_user = load_user(test_user.id)
        if loaded_user and loaded_user.username == 'testuser':
            print("✅ User loader working correctly")
        else:
            print("❌ User loader failed")
            
        # Clean up
        db.session.delete(test_user)
        db.session.commit()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()