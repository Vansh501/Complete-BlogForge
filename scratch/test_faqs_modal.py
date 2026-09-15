import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models import db, User

class FAQsModalTestCase(unittest.TestCase):
    def setUp(self):
        self.db_file = 'temp_test_faqs.db'
        if os.path.exists(self.db_file):
            try:
                os.remove(self.db_file)
            except Exception:
                pass
        os.environ['DATABASE_URL'] = f'sqlite:///{self.db_file}'
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

        # Seed test user
        self.user = User(username='testuser', email='test@example.com')
        self.user.set_password('pass123')
        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        if os.path.exists(self.db_file):
            try:
                os.remove(self.db_file)
            except Exception:
                pass

    def test_faqs_modal_rendered_for_logged_in_user(self):
        # Log in as testuser
        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(self.user.id)

        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)

        # Check for FAQs option in user dropdown menu
        self.assertIn(b'data-bs-target="#faqsModal"', resp.data)
        self.assertIn(b'FAQs', resp.data)

        # Check for interactive FAQs modal existence and title
        self.assertIn(b'id="faqsModal"', resp.data)
        self.assertIn(b'Frequently Asked Questions', resp.data)
        self.assertIn(b'What is AetherBlog?', resp.data)
        print("Verification passed: FAQs menu option and interactive modal verified successfully.")

if __name__ == '__main__':
    unittest.main()
