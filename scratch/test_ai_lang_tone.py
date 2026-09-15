import os
import sys
import unittest

# Adjust search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import User

class AILangToneTestCase(unittest.TestCase):
    def setUp(self):
        self.db_file = 'temp_test_ai_lang_tone.db'
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
        self.client = self.app.test_client()

        # Seed test user
        user = User(username='writer', email='writer@example.com')
        user.set_password('pass123')
        db.session.add(user)
        db.session.commit()
        self.user_id = user.id

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        if os.path.exists(self.db_file):
            try:
                os.remove(self.db_file)
            except Exception:
                pass

    def test_ai_assist_hindi_friendly(self):
        # Log in the user
        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(self.user_id)

        # Make AI assist call with hindi and friendly parameters
        resp = self.client.post('/ai/assist', json={
            'action': 'title',
            'topic': 'Machine Learning',
            'lang': 'hindi',
            'tone': 'friendly'
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        
        # Verify response contains the mock data translated or live result translated
        if 'mock_data' in data:
            self.assertIn('मार्गदर्शिका', data['mock_data'])
            self.assertIn('महत्वपूर्ण उपकरण', data['mock_data'])
        else:
            self.assertIn('result', data)
            # Unicode check for Devanagari (Hindi) script
            has_hindi = any('\u0900' <= char <= '\u097f' for char in data['result'])
            self.assertTrue(has_hindi, "Should return content written in Hindi script")
        print("AI assist Hindi translation verification passed.")

    def test_ai_assist_punjabi_friendly(self):
        # Log in the user
        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(self.user_id)

        # Make AI assist call with punjabi and friendly parameters
        resp = self.client.post('/ai/assist', json={
            'action': 'intro',
            'title': 'Technology',
            'lang': 'punjabi',
            'tone': 'friendly'
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        
        # Verify response contains the mock data in Punjabi script or live result
        if 'mock_data' in data:
            self.assertIn('ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ ਦੋਸਤੋ', data['mock_data'])
        else:
            self.assertIn('result', data)
            # Unicode check for Gurmukhi (Punjabi) script
            has_punjabi = any('\u0a00' <= char <= '\u0a7f' for char in data['result'])
            self.assertTrue(has_punjabi, "Should return content written in Punjabi script")
        print("AI assist Punjabi translation verification passed.")

    def test_ai_translate_action(self):
        # Log in the user
        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(self.user_id)

        # Make AI assist call with action == translate for gujarati
        resp = self.client.post('/ai/assist', json={
            'action': 'translate',
            'text_to_process': 'Hello World ||| Welcome to coding.',
            'lang': 'gujarati'
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()

        # Check translation result or mock_data contains Gurmukhi/Gujarati scripts
        if 'mock_data' in data:
            self.assertIn('સાચી', data['mock_data'])
            self.assertIn('સાચી મિત્રતા', data['mock_data'])
        else:
            self.assertIn('result', data)
            # Unicode check for Gujarati script: \u0a80 to \u0aff
            has_gujarati = any('\u0a80' <= char <= '\u0aff' for char in data['result'])
            self.assertTrue(has_gujarati, "Should return content written in Gujarati script")
        print("AI assist translate action verification passed.")

if __name__ == '__main__':
    unittest.main()
