import os
import sys

# Ensure project root is in PYTHONPATH
sys.path.insert(0, r"c:\Users\ASUS\OneDrive\Desktop\blog-system")

from app import create_app
from app.models import db, User, Post, Category, Tag

def test_search_and_sorting():
    db_file = 'temp_test_search.db'
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

            # Seed Authors
            author_alice = User(username='alice_writer', email='alice@test.com')
            author_alice.set_password('pass123')
            author_bob = User(username='bob_writer', email='bob@test.com')
            author_bob.set_password('pass123')
            db.session.add_all([author_alice, author_bob])
            db.session.commit()
            author_alice_id = author_alice.id

            # Seed Categories
            cat_tech = Category(name='Tech Trends', slug='tech-trends')
            cat_health = Category(name='Healthy Living', slug='healthy-living')
            db.session.add_all([cat_tech, cat_health])
            db.session.commit()

            # Seed Tags
            tag_flask = Tag(name='flask')
            tag_yoga = Tag(name='yoga')
            db.session.add_all([tag_flask, tag_yoga])
            db.session.commit()

            # Seed Posts
            # Post A: Title "Zeta Post", Category Tech, Tag Flask, Author Alice
            post_a = Post(
                title='Zeta Post',
                slug='zeta-post',
                content='Exploring Flask blueprints.',
                summary='Flask zeta',
                category_id=cat_tech.id,
                author_id=author_alice.id,
                status='Published'
            )
            post_a.tags.append(tag_flask)

            # Post B: Title "Alpha Post", Category Health, Tag Yoga, Author Alice
            post_b = Post(
                title='Alpha Post',
                slug='alpha-post',
                content='Exploring Yoga positions.',
                summary='Yoga alpha',
                category_id=cat_health.id,
                author_id=author_alice.id,
                status='Published'
            )
            post_b.tags.append(tag_yoga)

            # Post C: Title "Beta Post", Category Tech, Tag Yoga, Author Alice
            post_c = Post(
                title='Beta Post',
                slug='beta-post',
                content='Tech yoga integration.',
                summary='Tech yoga beta',
                category_id=cat_tech.id,
                author_id=author_alice.id,
                status='Published'
            )
            post_c.tags.append(tag_yoga)

            db.session.add_all([post_a, post_b, post_c])
            db.session.commit()

        # Log in author_alice to allow access to the private blog feed
        with client.session_transaction() as sess:
            sess['_user_id'] = str(author_alice_id)

        # 1. Test Search by Category Name ("Tech Trends")
        resp = client.get('/?q=Tech%20Trends')
        assert resp.status_code == 200
        feed_grid = resp.data.split(b'<!-- Sidebar Widget Column -->')[0]
        assert b'Zeta Post' in feed_grid
        assert b'Beta Post' in feed_grid
        assert b'Alpha Post' not in feed_grid
        print("Search by Category name verified successfully.")

        # 2. Test Search by Tag Name ("flask")
        resp = client.get('/?q=flask')
        assert resp.status_code == 200
        feed_grid = resp.data.split(b'<!-- Sidebar Widget Column -->')[0]
        assert b'Zeta Post' in feed_grid
        assert b'Beta Post' not in feed_grid
        assert b'Alpha Post' not in feed_grid
        print("Search by Tag name verified successfully.")

        # 3. Test Search by Author Username ("alice_writer")
        resp = client.get('/?q=alice_writer')
        assert resp.status_code == 200
        feed_grid = resp.data.split(b'<!-- Sidebar Widget Column -->')[0]
        assert b'Alpha Post' in feed_grid
        assert b'Zeta Post' in feed_grid
        assert b'Beta Post' in feed_grid
        print("Search by Author username verified successfully.")

        # 4. Test Search by Title ("Zeta")
        resp = client.get('/?q=Zeta')
        assert resp.status_code == 200
        feed_grid = resp.data.split(b'<!-- Sidebar Widget Column -->')[0]
        assert b'Zeta Post' in feed_grid
        assert b'Beta Post' not in feed_grid
        print("Search by Title keyword verified successfully.")

        # 5. Test Sorting Option: title_asc (Alpha -> Beta -> Zeta)
        resp = client.get('/?sort=title_asc')
        assert resp.status_code == 200
        p_alpha = resp.data.find(b'Alpha Post')
        p_beta = resp.data.find(b'Beta Post')
        p_zeta = resp.data.find(b'Zeta Post')
        assert p_alpha < p_beta < p_zeta, "Title ASC sorting order fail"
        print("Sort order Title (A-Z) verified successfully.")

        # 6. Test Sorting Option: title_desc (Zeta -> Beta -> Alpha)
        resp = client.get('/?sort=title_desc')
        assert resp.status_code == 200
        p_alpha = resp.data.find(b'Alpha Post')
        p_beta = resp.data.find(b'Beta Post')
        p_zeta = resp.data.find(b'Zeta Post')
        assert p_zeta < p_beta < p_alpha, "Title DESC sorting order fail"
        print("Sort order Title (Z-A) verified successfully.")

        # 7. Test Sorting Option: oldest (Post A -> Post B -> Post C)
        resp = client.get('/?sort=oldest')
        assert resp.status_code == 200
        p_a = resp.data.find(b'Zeta Post')
        p_b = resp.data.find(b'Alpha Post')
        p_c = resp.data.find(b'Beta Post')
        assert p_a < p_b < p_c, "Oldest first sorting order fail"
        print("Sort order Oldest First verified successfully.")

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
        test_search_and_sorting()
        print("\nAll search and sorting index checks passed successfully!")
    except AssertionError as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
