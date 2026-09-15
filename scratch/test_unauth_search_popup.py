import os
import sys

# Ensure project root is in PYTHONPATH
sys.path.insert(0, r"c:\Users\ASUS\OneDrive\Desktop\blog-system")

from app import create_app
from app.models import db, User

def test_unauth_search_popup():
    db_file = 'temp_test_unauth_search.db'
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except Exception:
            pass

    os.environ['DATABASE_URL'] = f'sqlite:///{db_file}'
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    with app.test_client() as client:
        with app.app_context():
            db.drop_all()
            db.create_all()

            # Seed user
            user = User(username='test_user', email='test@user.com')
            user.set_password('pass123')
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        # 1. Access landing page when NOT logged in
        resp_unauth = client.get('/')
        assert resp_unauth.status_code == 200
        # Assert the search interceptor JS block is present
        assert b'signup to create post' in resp_unauth.data
        assert b'Sign in to search articles...' in resp_unauth.data
        print("Unauthenticated search interceptor script presence verified on landing page.")

        # 2. Log in user and access home page when logged in
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user_id)

        resp_auth = client.get('/')
        assert resp_auth.status_code == 200
        # Assert the search interceptor JS block is NOT present
        assert b'signup to create post' not in resp_auth.data
        print("Authenticated search interceptor script absence verified on homepage.")

        # Cleanup database session
        try:
            with app.app_context():
                db.session.remove()
                db.drop_all()
        except Exception:
            pass

    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except Exception:
            pass

if __name__ == '__main__':
    try:
        test_unauth_search_popup()
        print("\nAll search popup verification tests passed successfully!")
    except AssertionError as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
