import os
import sys

# Ensure project root is in PYTHONPATH
sys.path.insert(0, r"c:\Users\ASUS\OneDrive\Desktop\blog-system")

from app import create_app
from app.models import db, User, Post

def test_featured_see_more():
    db_file = 'temp_test_featured_see_more.db'
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
            admin_id = admin.id

            # Seed 4 featured posts
            posts = []
            for i in range(1, 5):
                posts.append(Post(
                    title=f'Featured Article {i}',
                    slug=f'featured-article-{i}',
                    content=f'This is content of featured post {i}',
                    author_id=admin_id,
                    status='Published',
                    is_featured=True
                ))
            db.session.add_all(posts)
            db.session.commit()

        # Log in admin to bypass private blog redirect
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_id)

        # 1. Homepage should only render the most recent 3 featured posts
        home_resp = client.get('/')
        assert home_resp.status_code == 200
        
        # Get featured posts area (ends before grid feed)
        featured_area = home_resp.data.split(b'<!-- Grid Feed Layout -->')[0]
        
        # Should contain Featured Article 4, 3, 2 (descending)
        assert b'Featured Article 4' in featured_area
        assert b'Featured Article 3' in featured_area
        assert b'Featured Article 2' in featured_area
        assert b'Featured Article 1' not in featured_area # Only first 3 are shown
        
        # "See More" link should be present since total featured posts count = 4
        assert b'href="/featured"' in featured_area
        print("Homepage only renders 3 featured posts and includes See More link successfully.")

        # 2. Clicking "See More" /featured page should render all 4 featured posts
        feat_resp = client.get('/featured')
        assert feat_resp.status_code == 200
        assert b'Featured Article 4' in feat_resp.data
        assert b'Featured Article 3' in feat_resp.data
        assert b'Featured Article 2' in feat_resp.data
        assert b'Featured Article 1' in feat_resp.data # Now visible on see more page!
        print("Featured list page renders all featured posts successfully.")

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
        test_featured_see_more()
        print("\nAll featured See More checks passed successfully!")
    except AssertionError as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
