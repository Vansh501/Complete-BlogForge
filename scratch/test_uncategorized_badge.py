import os
import sys

# Ensure project root is in PYTHONPATH
sys.path.insert(0, r"c:\Users\ASUS\OneDrive\Desktop\blog-system")

from app import create_app
from app.models import db, User, Post

def test_uncategorized_badge():
    db_file = 'temp_test_uncategorized_badge.db'
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

            # Post without category
            p = Post(
                title='Unassigned category article',
                slug='unassigned-cat',
                content='Content of uncategorized post.',
                author_id=user_id,
                status='Published',
                category_id=None
            )
            db.session.add(p)
            db.session.commit()

        # Log in user
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user_id)

        # 1. Homepage card grid check
        home_resp = client.get('/')
        assert home_resp.status_code == 200
        assert b'Not Categorized' in home_resp.data
        print("Homepage uncategorized card badge verified successfully.")

        # 2. Post detail page check
        post_resp = client.get('/post/unassigned-cat')
        assert post_resp.status_code == 200
        assert b'Not Categorized' in post_resp.data
        print("Post detail page uncategorized badge verified successfully.")

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
        test_uncategorized_badge()
        print("\nAll uncategorized badge checks passed successfully!")
    except AssertionError as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
