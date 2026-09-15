import os
import sys

# Ensure project root is in PYTHONPATH
sys.path.insert(0, r"c:\Users\ASUS\OneDrive\Desktop\blog-system")

from app import create_app
from app.models import db, User, Post

def test_summary_and_content_striptags():
    db_file = 'temp_test_striptags.db'
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
            user = User(username='test_editor', email='editor@test.com')
            user.set_password('pass123')
            db.session.add(user)
            db.session.commit()
            user_id = user.id

            # Post with HTML content & empty summary (falls back to content)
            p1 = Post(
                title='Laptop buying guide',
                slug='laptop-buying',
                content='<p><br></p><p><br></p><h3>Introduction to Laptop Buying</h3><p>With the numerous options available in the market, buying a laptop can be a daunting task.</p>',
                summary='',
                author_id=user_id,
                status='Published'
            )
            # Post with tags in summary
            p2 = Post(
                title='Chair styles decors',
                slug='chair-styles',
                content='Simple content.',
                summary='<p>Get ready to take a seat in style! When it comes to home decor, the humble chair is often overlooked.</p>',
                author_id=user_id,
                status='Published'
            )
            db.session.add_all([p1, p2])
            db.session.commit()

        # Log in user
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user_id)

        # Access homepage feed
        resp = client.get('/')
        assert resp.status_code == 200

        # Assert no literal tags appear in the HTML response overview cards
        assert b'&lt;p&gt;' not in resp.data
        assert b'&lt;br&gt;' not in resp.data
        assert b'&lt;h3&gt;' not in resp.data
        assert b'<p><br>' not in resp.data
        assert b'<h3>Introduction' not in resp.data
        
        # Verify content text is present without tags
        assert b'Introduction to Laptop Buying' in resp.data
        assert b'Get ready to take a seat' in resp.data
        print("Literal HTML tags successfully stripped from all overview summaries.")

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
        test_summary_and_content_striptags()
        print("\nAll striptags verification tests passed successfully!")
    except AssertionError as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
