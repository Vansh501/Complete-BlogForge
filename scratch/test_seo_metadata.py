import os
import sys

# Ensure project root is in PYTHONPATH
sys.path.insert(0, r"c:\Users\ASUS\OneDrive\Desktop\blog-system")

from app import create_app
from app.models import db, User, Post, Category, Tag

def test_seo_metadata_endpoints():
    db_file = 'temp_test_seo.db'
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
            admin = User(username='admin_boss', email='boss@test.com')
            admin.set_password('pass123')
            db.session.add(admin)
            db.session.commit()
            admin_id = admin.id

            # Seed category
            cat = Category(name='Dev Ops', slug='dev-ops')
            db.session.add(cat)
            db.session.commit()

            # Seed published post
            p = Post(
                title='Flask Server Optimizations',
                slug='flask-server-opts',
                content='Detailed production server setups.',
                summary='Speed up Flask responses.',
                category_id=cat.id,
                author_id=admin.id,
                status='Published'
            )
            db.session.add(p)
            db.session.commit()

        # Log in admin to allow access to the private blog feed
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_id)

        # 1. Verify robots.txt
        robots_resp = client.get('/robots.txt')
        assert robots_resp.status_code == 200
        assert b'User-agent: *' in robots_resp.data
        assert b'Sitemap:' in robots_resp.data
        assert robots_resp.headers['Content-Type'].startswith('text/plain')
        print("robots.txt endpoint verification passed.")

        # 2. Verify sitemap.xml
        sitemap_resp = client.get('/sitemap.xml')
        assert sitemap_resp.status_code == 200
        assert sitemap_resp.headers['Content-Type'].startswith('application/xml')
        # Check URLs inside sitemap
        assert b'/about' in sitemap_resp.data
        assert b'/contact' in sitemap_resp.data
        assert b'/post/flask-server-opts' in sitemap_resp.data
        assert b'/category/dev-ops' in sitemap_resp.data
        print("sitemap.xml dynamically generated elements verification passed.")

        # 3. Verify Homepage Meta & OG tags
        home_resp = client.get('/')
        assert home_resp.status_code == 200
        assert b'<title>Home | AetherBlog</title>' in home_resp.data
        assert b'<meta name="description" content="AetherBlog - A modern publishing platform' in home_resp.data
        assert b'<meta property="og:type" content="website">' in home_resp.data
        assert b'<meta name="twitter:card" content="summary_large_image">' in home_resp.data
        print("Homepage base layout SEO and OG tags verification passed.")

        # 4. Verify Post detail Meta & OG tags
        post_resp = client.get('/post/flask-server-opts')
        assert post_resp.status_code == 200
        assert b'<title>Flask Server Optimizations | AetherBlog</title>' in post_resp.data
        assert b'<meta name="description" content="Speed up Flask responses.' in post_resp.data
        assert b'<meta property="og:type" content="article">' in post_resp.data
        print("Post detail customized SEO overrides verification passed.")

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
        test_seo_metadata_endpoints()
        print("\nAll SEO & Sitemap metadata checks passed successfully!")
    except AssertionError as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
