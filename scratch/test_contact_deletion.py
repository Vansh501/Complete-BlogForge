import os
import sys

# Ensure project root is in PYTHONPATH
sys.path.insert(0, r"c:\Users\ASUS\OneDrive\Desktop\blog-system")

from app import create_app
from app.models import db, User, ContactMessage

def test_contact_form_and_deletion():
    db_file = 'temp_test_contact.db'
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

            # Seed admin user
            admin = User(username='admin_boss', email='boss@test.com', is_admin=True)
            admin.set_password('pass123')
            db.session.add(admin)
            db.session.commit()

        # 1. Visitor submits contact form
        contact_data = {
            'name': 'Visitor Alice',
            'email': 'alice@test.com',
            'subject': 'Technical Support',
            'message': 'Can you explain where to put the keys?'
        }
        submit_resp = client.post('/contact', data=contact_data, follow_redirects=True)
        assert submit_resp.status_code == 200
        assert b'Your message has been sent' in submit_resp.data or b'sent successfully' in submit_resp.data

        # Verify DB
        with app.app_context():
            db.session.remove()
            msg = ContactMessage.query.first()
            assert msg is not None
            assert msg.name == 'Visitor Alice'
            assert msg.subject == 'Technical Support'
        print("Visitor contact form submission verified successfully.")

        # 2. Log in admin client
        login_resp = client.post('/login', data={'login_credential': 'admin_boss', 'password': 'pass123'})
        assert login_resp.status_code == 302

        # 3. View inbox and assert message appears
        inbox_resp = client.get('/admin/messages')
        assert inbox_resp.status_code == 200
        assert b'Technical Support' in inbox_resp.data
        assert b'Visitor Alice' in inbox_resp.data
        print("Admin messages inbox loads successfully and displays new message.")

        # 4. Admin deletes message via POST
        del_resp = client.post('/admin/messages/delete/1', follow_redirects=True)
        assert del_resp.status_code == 200
        assert b'deleted successfully' in del_resp.data

        # Verify DB
        with app.app_context():
            db.session.remove()
            assert ContactMessage.query.get(1) is None
        print("Admin delete message endpoint verified successfully.")

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
        test_contact_form_and_deletion()
        print("\nAll contact page & message inbox CRUD checks passed successfully!")
    except AssertionError as e:
        print(f"\nTest Assertion failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error running tests: {e}", file=sys.stderr)
        sys.exit(1)
