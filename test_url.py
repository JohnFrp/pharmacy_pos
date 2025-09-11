from app import create_app

app = create_app()

with app.app_context():
    with app.test_client() as client:
        # Test all main URLs
        urls_to_test = [
            '/',
            '/auth/login',
            '/auth/register',
            '/auth/logout',
            '/admin',
            '/inventory',
            '/sales',
            '/customers',
            '/reports'
        ]
        
        for url in urls_to_test:
            try:
                response = client.get(url, follow_redirects=True)
                print(f"✅ {url} - {response.status_code}")
            except Exception as e:
                print(f"❌ {url} - Error: {str(e)}")