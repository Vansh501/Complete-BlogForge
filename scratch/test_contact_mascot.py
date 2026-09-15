import os
import sys

# Ensure project root is in PYTHONPATH
sys.path.insert(0, r"c:\Users\ASUS\OneDrive\Desktop\blog-system")

from app import create_app
from app.models import db

def test_contact_mascot_widget():
    db_file = 'temp_test_mascot.db'
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

        # Access Contact page
        resp = client.get('/contact')
        assert resp.status_code == 200
        
        # Verify mascot widget DOM elements presence
        assert b'Office Mascots' in resp.data
        assert b'mascot-card' in resp.data
        assert b'btn-mascot-cat' in resp.data
        assert b'btn-mascot-dog' in resp.data
        assert b'mascot-image-cat' in resp.data
        assert b'mascot-image-dog' in resp.data
        assert b'Luna' in resp.data
        print("Contact page mascot card and elements verified successfully.")

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
        test_contact_mascot_widget()
        print("\nAll mascot widget verification tests passed successfully!")
    except AssertionError as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
