import os
import sys

# Ensure project root is in PYTHONPATH
sys.path.insert(0, r"c:\Users\ASUS\OneDrive\Desktop\blog-system")

from app import create_app
from app.models import db, User

def test_editor_tip_rotator():
    db_file = 'temp_test_rotator.db'
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
            user = User(username='test_writer', email='writer@test.com')
            user.set_password('pass123')
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        # Log in user
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user_id)

        # Access write post editor page
        resp = client.get('/post/create')
        assert resp.status_code == 200
        
        # Verify tip widget presence
        assert b'CO-PILOT INSIGHT' in resp.data
        assert b'ai-tip-widget' in resp.data
        assert b'ai-tip-item' in resp.data
        
        # Verify 3 tips content
        assert b'Start with a question' in resp.data
        assert b'Punchy layout' in resp.data
        assert b'Relevant tagging' in resp.data
        print("Editor rotating tips panel and contents verified successfully.")

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
        test_editor_tip_rotator()
        print("\nAll rotator verification tests passed successfully!")
    except AssertionError as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
