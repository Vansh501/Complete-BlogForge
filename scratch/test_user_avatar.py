import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models import db, User

class UserAvatarTestCase(unittest.TestCase):
    def setUp(self):
        self.db_file = 'temp_test_avatar.db'
        if os.path.exists(self.db_file):
            try:
                os.remove(self.db_file)
            except Exception:
                pass
        os.environ['DATABASE_URL'] = f'sqlite:///{self.db_file}'
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        if os.path.exists(self.db_file):
            try:
                os.remove(self.db_file)
            except Exception:
                pass

    def test_cool_svg_avatar_returned(self):
        user_alpha = User(username='alpha', email='alpha@example.com')
        user_alpha.set_password('pass123')
        user_beta = User(username='beta', email='beta@example.com')
        user_beta.set_password('pass123')
        db.session.add(user_alpha)
        db.session.add(user_beta)
        db.session.commit()

        # Retrieve default avatars
        avatar_alpha = user_alpha.get_avatar()
        avatar_beta = user_beta.get_avatar()

        # Verify they are base64-encoded SVG data URIs
        self.assertTrue(avatar_alpha.startswith('data:image/svg+xml;base64,'))
        self.assertTrue(avatar_beta.startswith('data:image/svg+xml;base64,'))

        # Decode and make sure they contain SVG tags
        import base64
        decoded_alpha = base64.b64decode(avatar_alpha.split(',')[1]).decode('utf-8')
        decoded_beta = base64.b64decode(avatar_beta.split(',')[1]).decode('utf-8')

        self.assertIn('<svg', decoded_alpha)
        self.assertIn('</svg>', decoded_alpha)
        self.assertIn('<svg', decoded_beta)
        self.assertIn('</svg>', decoded_beta)

    def test_preset_avatar_selection(self):
        user_gamma = User(username='gamma', email='gamma@example.com')
        user_gamma.set_password('pass123')
        db.session.add(user_gamma)
        db.session.commit()

        app_client = self.app.test_client()
        with app_client.session_transaction() as sess:
            sess['_user_id'] = str(user_gamma.id)

        # Submit update profile request selecting preset avatar 3
        resp = app_client.post('/profile', data={
            'action': 'update_info',
            'username': 'gamma',
            'email': 'gamma@example.com',
            'preset_avatar': 'avatar3'
        })
        self.assertEqual(resp.status_code, 302)

        # Reload user from DB and check avatar URL
        db.session.refresh(user_gamma)
        self.assertEqual(user_gamma.avatar_url, '/static/images/avatar3.svg')
        self.assertEqual(user_gamma.get_avatar(), '/static/images/avatar3.svg')
        print("Verification passed: Preset avatar selected and updated successfully.")

if __name__ == '__main__':
    unittest.main()
