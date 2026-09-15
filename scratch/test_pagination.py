import os
import sys

# Ensure project root is in PYTHONPATH
sys.path.insert(0, r"c:\Users\ASUS\OneDrive\Desktop\blog-system")

from app import create_app
from app.models import db, User, Post, Category

def test_pagination_limits():
    db_file = 'temp_test_paginate.db'
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
            writer = User(username='paginate_writer', email='paginate@writer.com')
            writer.set_password('pass123')
            db.session.add(writer)
            db.session.commit()
            writer_id = writer.id

            # Seed category
            cat = Category(name='Paginated Cat', slug='paginated-cat')
            db.session.add(cat)
            db.session.commit()

            # Seed 13 published posts
            from datetime import datetime, timedelta
            posts = []
            for i in range(1, 14):
                posts.append(Post(
                    title=f'Article Post {i:02d}',
                    slug=f'article-post-{i:02d}',
                    content=f'This is the body of paginated post number {i}. Search keyword: paginationterm.',
                    category_id=cat.id,
                    author_id=writer.id,
                    status='Published',
                    created_at=datetime.utcnow() - timedelta(minutes=(14-i))
                ))
            db.session.add_all(posts)
            db.session.commit()

        # Log in writer to allow access to the private blog feed
        with client.session_transaction() as sess:
            sess['_user_id'] = str(writer_id)

        # 1. Homepage Pagination (Page 1) - Default Homepage is capped at 3 posts
        resp_h1 = client.get('/')
        assert resp_h1.status_code == 200
        feed_grid = resp_h1.data.split(b'<!-- Sidebar Widget Column -->')[0]
        # Should contain Article Post 13 down to Article Post 11 (3 posts)
        assert b'Article Post 13' in feed_grid
        assert b'Article Post 11' in feed_grid
        assert b'Article Post 10' not in feed_grid # Should not show post 10
        # "See All Posts" button should be present
        assert b'See All Posts' in feed_grid
        assert b'href="/?author=paginate_writer"' in feed_grid
        print("Homepage default cap checks (3 posts maximum + See All Posts transition button) passed.")

        # 2. Author Feed Pagination (Page 1) - Shows 6 posts per page
        resp_a1 = client.get('/?author=paginate_writer')
        assert resp_a1.status_code == 200
        feed_grid = resp_a1.data.split(b'<!-- Sidebar Widget Column -->')[0]
        assert b'Article Post 13' in feed_grid
        assert b'Article Post 08' in feed_grid
        assert b'Article Post 07' not in feed_grid
        assert b'page=2' in feed_grid
        print("Author Feed Page 1 checks (6 posts maximum) passed.")

        # 3. Author Feed Pagination (Page 2) - Shows next 6 posts
        resp_a2 = client.get('/?author=paginate_writer&page=2')
        assert resp_a2.status_code == 200
        feed_grid = resp_a2.data.split(b'<!-- Sidebar Widget Column -->')[0]
        assert b'Article Post 07' in feed_grid
        assert b'Article Post 02' in feed_grid
        assert b'Article Post 13' not in feed_grid
        assert b'Article Post 01' not in feed_grid
        print("Author Feed Page 2 checks (posts 7-12) passed.")

        # 3b. Author Feed Pagination (Page 3) - Shows final post
        resp_a3 = client.get('/?author=paginate_writer&page=3')
        assert resp_a3.status_code == 200
        feed_grid = resp_a3.data.split(b'<!-- Sidebar Widget Column -->')[0]
        assert b'Article Post 01' in feed_grid
        assert b'Article Post 02' not in feed_grid
        print("Author Feed Page 3 checks (final post 13) passed.")

        # 4. Category Pagination (Page 1)
        resp_c1 = client.get('/category/paginated-cat')
        assert resp_c1.status_code == 200
        feed_grid = resp_c1.data.split(b'<!-- Sidebar Widget Column -->')[0]
        assert b'Article Post 13' in feed_grid
        assert b'Article Post 08' in feed_grid
        assert b'Article Post 07' not in feed_grid
        assert b'page=2' in feed_grid
        print("Category Detail Page 1 pagination checks passed.")

        # 5. Search Pagination (Page 1)
        resp_s1 = client.get('/?q=paginationterm')
        assert resp_s1.status_code == 200
        feed_grid = resp_s1.data.split(b'<!-- Sidebar Widget Column -->')[0]
        assert b'Article Post 13' in feed_grid
        assert b'Article Post 08' in feed_grid
        assert b'Article Post 07' not in feed_grid
        assert b'page=2' in feed_grid
        print("Search results Page 1 pagination checks passed.")

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
        test_pagination_limits()
        print("\nAll pagination verification checks passed successfully!")
    except AssertionError as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
