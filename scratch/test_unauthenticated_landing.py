import os
import sys

# Ensure project root is in PYTHONPATH
sys.path.insert(0, r"c:\Users\ASUS\OneDrive\Desktop\blog-system")

from app import create_app
from app.models import db, User, Post, Category, Tag

def test_unauthenticated_private_blog():
    db_file = 'temp_test_unauth.db'
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

            # Seed user, category, tag and post
            writer = User(username='writer_jane', email='jane@test.com')
            writer.set_password('pass123')
            db.session.add(writer)
            db.session.commit()

            cat = Category(name='Science Tech', slug='science-tech')
            t = Tag(name='physics')
            db.session.add_all([cat, t])
            db.session.commit()

            p = Post(
                title='Quantum Entanglement Explored',
                slug='quantum-entanglement',
                content='Exploring physics quantum entanglements.',
                category_id=cat.id,
                author_id=writer.id,
                status='Published'
            )
            p.tags.append(t)
            db.session.add(p)
            db.session.commit()

        # 1. Unauthenticated Home Page (should show interactive landing, NO blog feed)
        resp_home = client.get('/')
        assert resp_home.status_code == 200
        assert b'Creative Space' in resp_home.data
        assert b'AetherAI Simulator' in resp_home.data
        assert b'Latest Articles' not in resp_home.data
        assert b'Search Feed' not in resp_home.data
        print("Unauthenticated visitor homepage displays interactive landing and blocks blog content successfully.")

        # 2. Unauthenticated Post Detail (should redirect to home with warning)
        resp_post = client.get('/post/quantum-entanglement', follow_redirects=True)
        assert resp_post.status_code == 200
        assert b'Please log in to read this article' in resp_post.data
        assert b'Creative Space' in resp_post.data # landed back on landing page
        print("Unauthenticated post detail access redirected to landing successfully.")

        # 3. Unauthenticated Category Detail (should redirect to home with warning)
        resp_cat = client.get('/category/science-tech', follow_redirects=True)
        assert resp_cat.status_code == 200
        assert b'Please log in to browse categories' in resp_cat.data
        print("Unauthenticated category detail access redirected to landing successfully.")

        # 4. Unauthenticated Tag Detail (should redirect to home with warning)
        resp_tag = client.get('/tag/physics', follow_redirects=True)
        assert resp_tag.status_code == 200
        assert b'Please log in to browse tags' in resp_tag.data
        print("Unauthenticated tag detail access redirected to landing successfully.")

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
        test_unauthenticated_private_blog()
        print("\nAll unauthenticated visitor privacy checks passed successfully!")
    except AssertionError as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
