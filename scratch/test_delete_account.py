import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models import db, User, Post, Category

class DeleteAccountTestCase(unittest.TestCase):
    def setUp(self):
        self.db_file = 'temp_test_delete.db'
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
        
        # Seed test user
        self.user = User(username='deluser', email='del@example.com')
        self.user.set_password('pass123')
        db.session.add(self.user)
        db.session.commit()

        # Seed a post
        self.post = Post(
            title='Delete Me',
            content='Some post content to be deleted.',
            status='Published',
            slug='delete-me',
            author_id=self.user.id,
            category_id=self.cat_tech.id
        )
        db.session.add(self.post)
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

    def test_delete_account_removes_user_and_posts(self):
        # Log in as deluser
        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(self.user.id)

        # Trigger delete account POST route
        resp = self.client.post('/profile/delete')
        self.assertEqual(resp.status_code, 302)

        # Verify user is redirected to index landing page
        self.assertEqual(resp.location, '/')

        # Verify user record is deleted
        deleted_user = User.query.filter_by(username='deluser').first()
        self.assertIsNone(deleted_user)

        # Verify cascade deletes post as well
        deleted_post = Post.query.filter_by(title='Delete Me').first()
        self.assertIsNone(deleted_post)

        print("Verification passed: Account and associated posts permanently deleted.")

if __name__ == '__main__':
    unittest.main()
