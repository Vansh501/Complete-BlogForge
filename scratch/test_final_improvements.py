import os
import sys

# Ensure project root is in PYTHONPATH
sys.path.insert(0, r"c:\Users\ASUS\OneDrive\Desktop\blog-system")

from app import create_app

def test_final_improvements_and_errors():
    app = create_app()
    app.config['TESTING'] = False
    app.config['PROPAGATE_EXCEPTIONS'] = False
    app.config['WTF_CSRF_ENABLED'] = False  # Disable in tests to bypass token verification

    # Register simulated 500 route
    @app.route('/trigger-500')
    def trigger_500():
        raise Exception("Simulated internal server error")

    with app.test_client() as client:
        # 1. Test 404 error page
        resp_404 = client.get('/this-path-should-not-exist-at-all')
        assert resp_404.status_code == 404
        assert b'Lost in the Aether' in resp_404.data
        assert b'Return to Homepage' in resp_404.data
        print("Custom 404 Error handler and template verified successfully.")

        # 2. Test 500 error page
        resp_500 = client.get('/trigger-500')
        assert resp_500.status_code == 500
        assert b'Internal Server Error' in resp_500.data
        assert b'Something went wrong on our servers' in resp_500.data
        print("Custom 500 Error handler and template verified successfully.")

        # 3. Verify top loading bar is rendered on homepage
        home_resp = client.get('/')
        assert home_resp.status_code == 200
        assert b'id="top-loading-bar"' in home_resp.data
        print("Top Loading progress bar element presence verified.")

        # 4. Verify CSRF extension is initialized
        assert 'csrf' in app.extensions, "CSRFProtect was not initialized on the application"
        print("CSRF protection extension presence verified.")

if __name__ == '__main__':
    try:
        test_final_improvements_and_errors()
        print("\nAll final improvements checks passed successfully!")
    except AssertionError as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
