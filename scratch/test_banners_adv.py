import os
import sys
from io import BytesIO

# Ensure project root is in PYTHONPATH
sys.path.insert(0, r"c:\Users\ASUS\OneDrive\Desktop\blog-system")

from app import create_app
from app.models import db, User, Banner

def test_admin_banner_management():
    db_file = 'temp_test_banners.db'
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except Exception:
            pass

    os.environ['DATABASE_URL'] = f'sqlite:///{db_file}'
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    # Set fake uploads directory
    app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'uploads')

    with app.test_client() as client:
        with app.app_context():
            db.drop_all()
            db.create_all()

            # Seed admin user
            admin = User(username='admin_boss', email='boss@test.com', is_admin=True)
            admin.set_password('pass123')
            db.session.add(admin)
            db.session.commit()

        # Log in admin client
        login_resp = client.post('/login', data={'login_credential': 'admin_boss', 'password': 'pass123'})
        assert login_resp.status_code == 302

        # 1. Add Banner via POST (using multipart/form-data upload)
        banner_image = (BytesIO(b"dummy image data"), "banner1.png")
        data = {
            'title': 'Aether Engine',
            'subtitle': 'Fast AI writing support',
            'banner_image_file': banner_image,
            'link_url': 'https://aetherblog.dev/engine',
            'button_text': 'Launch Engine',
            'display_order': '2',
            'active': 'on'
        }
        add_resp = client.post('/admin/banners', data=data, content_type='multipart/form-data', follow_redirects=True)
        assert add_resp.status_code == 200
        assert b'added successfully' in add_resp.data
        
        # Verify in DB
        with app.app_context():
            db.session.remove()
            b1 = Banner.query.get(1)
            assert b1.title == 'Aether Engine'
            assert b1.display_order == 2
            assert b1.button_text == 'Launch Engine'
            assert b1.active is True
        print("Admin add banner workflow verified successfully.")

        # 2. Add second banner with lower display order (display_order = 1)
        banner_image_2 = (BytesIO(b"dummy image data 2"), "banner2.png")
        data_2 = {
            'title': 'Interactive CLI Tool',
            'subtitle': 'Manage posts on CLI',
            'banner_image_file': banner_image_2,
            'link_url': 'https://aetherblog.dev/cli',
            'button_text': 'Get CLI',
            'display_order': '1',
            'active': 'on'
        }
        add_resp_2 = client.post('/admin/banners', data=data_2, content_type='multipart/form-data', follow_redirects=True)
        assert add_resp_2.status_code == 200

        # Verify ordering on homepage
        home_resp = client.get('/')
        assert home_resp.status_code == 200
        # Banner 2 (display_order 1) must appear before Banner 1 (display_order 2) in HTML rendering sequence
        pos_b2 = home_resp.data.find(b'Interactive CLI Tool')
        pos_b1 = home_resp.data.find(b'Aether Engine')
        assert pos_b2 != -1
        assert pos_b1 != -1
        assert pos_b2 < pos_b1, "Banners should be sorted by display_order ascending"
        print("Dynamic banners display order sorting verified successfully on homepage.")

        # 3. Edit Banner 1 (Aether Engine -> Cloud Engine, display_order 2 -> 0)
        # Leave banner_image_file empty to test preserving current cover photo
        data_edit = {
            'title': 'Cloud Engine',
            'subtitle': 'Fast AI writing support',
            'banner_image_file': (BytesIO(b""), ""), # Empty upload
            'link_url': 'https://aetherblog.dev/cloud',
            'button_text': 'Launch Cloud',
            'display_order': '0',
            'active': 'on'
        }
        edit_resp = client.post('/admin/banners/edit/1', data=data_edit, content_type='multipart/form-data', follow_redirects=True)
        assert edit_resp.status_code == 200
        assert b'updated successfully' in edit_resp.data

        # Verify database details
        with app.app_context():
            db.session.remove()
            updated_b1 = Banner.query.get(1)
            assert updated_b1.title == 'Cloud Engine'
            assert updated_b1.display_order == 0
            assert updated_b1.button_text == 'Launch Cloud'
            assert updated_b1.image_url.startswith('/static/uploads/banners/')
        print("Admin edit banner workflow verified successfully.")

        # 4. Delete Banner 2
        del_resp = client.post('/admin/banners/delete/2', follow_redirects=True)
        assert del_resp.status_code == 200
        assert b'deleted successfully' in del_resp.data

        with app.app_context():
            db.session.remove()
            assert Banner.query.get(2) is None
        print("Admin delete banner workflow verified successfully.")

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
        test_admin_banner_management()
        print("\nAll dynamic hero banners management checks passed successfully!")
    except AssertionError as e:
        print(f"\nTest Assertion failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error running tests: {e}", file=sys.stderr)
        sys.exit(1)
