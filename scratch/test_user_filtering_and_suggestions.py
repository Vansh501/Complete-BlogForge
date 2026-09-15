import os
import sys
import unittest

# Ensure project root is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models import db, User, Post, Category

class UserFilteringAndSuggestionsTestCase(unittest.TestCase):
    def setUp(self):
        self.db_file = 'temp_test_user_filtering.db'
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

        # Seed categories
        self.cat_tech = Category(name='Tech', slug='tech')
        db.session.add(self.cat_tech)
        
        # Seed user vansh
        self.user_vansh = User(username='vansh', email='vansh@example.com')
        self.user_vansh.set_password('pass123')
        db.session.add(self.user_vansh)
        
        # Seed user max (new user with 0 posts)
        self.user_max = User(username='max', email='max@example.com')
        self.user_max.set_password('pass123')
        db.session.add(self.user_max)
        db.session.commit()

        # Seed a post for vansh
        self.post_vansh = Post(
            title='Vansh Tech Article',
            content='This is some tech post content.',
            status='Published',
            slug='vansh-tech-article',
            author_id=self.user_vansh.id,
            category_id=self.cat_tech.id
        )
        db.session.add(self.post_vansh)
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

    def test_user_vansh_sees_only_own_posts(self):
        # Log in as vansh
        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(self.user_vansh.id)

        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        # Vansh should see their own post
        self.assertIn(b'Vansh Tech Article', resp.data)
        # Vansh has 1 post, so should NOT see AI Suggestions block
        self.assertNotIn(b'AI Copilot Suggested Drafts', resp.data)
        print("Verification passed: User Vansh sees only own posts, suggestions hidden.")

    def test_user_max_sees_suggestions(self):
        # Log in as max
        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(self.user_max.id)

        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        # Max has 0 posts, so should NOT see Vansh's post on homepage
        self.assertNotIn(b'Vansh Tech Article', resp.data)
        # Max should see the AI suggestions block
        self.assertIn(b'AI Copilot Suggested Drafts', resp.data)
        # Max should see suggested topics sub-navbar
        self.assertIn(b'AI Suggestions', resp.data)
        print("Verification passed: New User Max sees AI suggested drafts and topics sub-navbar.")

if __name__ == '__main__':
    unittest.main()
