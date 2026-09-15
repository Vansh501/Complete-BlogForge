import os
import sys

# Ensure project root is in PYTHONPATH
sys.path.insert(0, r"c:\Users\ASUS\OneDrive\Desktop\blog-system")

from app import create_app
from app.models import db, User, Post, Category, Tag

def test_author_filter_no_prefill():
    db_file = 'temp_test_author_filter.db'
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

            # Seed users and posts
            user_vansh = User(username='vansh', email='vansh@test.com')
            user_vansh.set_password('pass123')
            
            user_jane = User(username='jane', email='jane@test.com')
            user_jane.set_password('pass123')
            
            db.session.add_all([user_vansh, user_jane])
            db.session.commit()

            p1 = Post(
                title='Vansh Quantum Tech Post',
                slug='vansh-quantum-tech',
                content='Physics by Vansh.',
                author_id=user_vansh.id,
                status='Published'
            )
            p2 = Post(
                title='Jane Chemistry Tech Post',
                slug='jane-chemistry-tech',
                content='Chemistry by Jane.',
                author_id=user_jane.id,
                status='Published'
            )
            db.session.add_all([p1, p2])
            db.session.commit()
            
            user_vansh_id = user_vansh.id

        # Log in user to view index page blog feed
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user_vansh_id)

        # 1. Access homepage with author filter parameter
        resp = client.get('/?author=vansh')
        assert resp.status_code == 200
        # Check that we only see Vansh's post in the main post list feed
        feed_grid = resp.data.split(b'<!-- Sidebar Widget Column -->')[0]
        assert b'Vansh Quantum Tech Post' in feed_grid
        assert b'Jane Chemistry Tech Post' not in feed_grid
        
        # Check that the search text input fields do NOT contain "vansh" value
        # They should be empty: value="" or value="{{ search_query }}" -> which is empty string
        # e.g., name="q" placeholder="Enter keywords..." value="" (no prefill)
        assert b'name="q" placeholder="Enter keywords..." value=""' in resp.data or b'name="q" placeholder="Enter keywords..." value="' not in resp.data or b'value="vansh"' not in resp.data
        
        # Also check the top navbar search:
        # e.g., name="q" placeholder="Search posts, topics or authors..." value=""
        assert b'name="q" placeholder="Search posts, topics or authors..." value="vansh"' not in resp.data

        # Check the active filter badge shows "Author: vansh"
        assert b'Author: vansh' in resp.data
        print("Author filter does not prefill search input field value successfully.")

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
        test_author_filter_no_prefill()
        print("\nAll author filter param tests passed successfully!")
    except AssertionError as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
