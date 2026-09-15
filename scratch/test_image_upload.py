import os
import sys
from io import BytesIO
from PIL import Image

# Ensure project root is in PYTHONPATH
sys.path.insert(0, r"c:\Users\ASUS\OneDrive\Desktop\blog-system")

from app import create_app
from app.models import db, User, Post

def test_image_upload_and_processing():
    db_file = 'temp_test_image.db'
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except Exception:
            pass

    os.environ['DATABASE_URL'] = f'sqlite:///{db_file}'
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    # Configure actual upload folders
    static_uploads = os.path.join(app.static_folder, 'uploads')
    app.config['UPLOAD_FOLDER'] = static_uploads
    os.makedirs(static_uploads, exist_ok=True)

    with app.test_client() as client:
        with app.app_context():
            db.drop_all()
            db.create_all()

            # Seed user
            u = User(username='writer_boss', email='writer@test.com')
            u.set_password('pass123')
            db.session.add(u)
            db.session.commit()

        # Log in
        login_resp = client.post('/login', data={'login_credential': 'writer_boss', 'password': 'pass123'})
        assert login_resp.status_code == 302

        # Create a mock large image (1600 x 900)
        im = Image.new('RGB', (1600, 900), color='blue')
        img_io = BytesIO()
        im.save(img_io, 'JPEG')
        img_io.seek(0)
        
        post_image = (img_io, "large_cover.jpg")

        # 1. Create post with large featured image upload
        data_create = {
            'title': 'Test Image Post',
            'content': 'Validating Pillow scaling filters.',
            'featured_image_file': post_image,
            'status': 'Published'
        }
        create_resp = client.post('/post/create', data=data_create, content_type='multipart/form-data', follow_redirects=True)
        assert create_resp.status_code == 200
        assert b'created successfully' in create_resp.data

        # Verify DB and check dimensions
        with app.app_context():
            db.session.remove()
            p = Post.query.first()
            assert p is not None
            assert p.featured_image.startswith('/static/uploads/posts/')
            
            # Read saved file on disk to check resizing
            saved_rel_path = p.featured_image.lstrip('/')
            saved_full_path = os.path.join(app.root_path, saved_rel_path)
            assert os.path.exists(saved_full_path)
            
            # Verify width is resized to 1200
            with Image.open(saved_full_path) as saved_img:
                w, h = saved_img.size
                assert w == 1200, f"Expected width to be resized to 1200, got {w}"
                assert h == 675, f"Expected height to scale proportionally to 675, got {h}"
            print("Pillow image resizing and upload verification passed successfully.")

            # Keep path for cleanup check
            initial_path = saved_full_path

        # 2. Update post to clear image and assert file is deleted from disk
        data_edit_clear = {
            'title': 'Test Image Post',
            'content': 'Validating Pillow scaling filters.',
            'clear_featured_image': 'true',
            'featured_image_file': (BytesIO(b""), ""),
            'status': 'Published'
        }
        edit_resp = client.post('/post/edit/1', data=data_edit_clear, content_type='multipart/form-data', follow_redirects=True)
        assert edit_resp.status_code == 200
        assert b'updated successfully' in edit_resp.data

        # Verify DB is cleared and file on disk is deleted
        with app.app_context():
            db.session.remove()
            p = Post.query.first()
            assert p.featured_image is None
            assert not os.path.exists(initial_path), "Old cover image file was not deleted from disk"
        print("Clear image and disk file deletion verification passed successfully.")

        # 3. Create another image, upload, then delete post
        im2 = Image.new('RGB', (800, 600), color='green')
        img_io2 = BytesIO()
        im2.save(img_io2, 'PNG')
        img_io2.seek(0)

        data_edit_upload = {
            'title': 'Test Image Post',
            'content': 'Validating Pillow scaling filters.',
            'featured_image_file': (img_io2, "green_cover.png"),
            'status': 'Published'
        }
        edit_resp2 = client.post('/post/edit/1', data=data_edit_upload, content_type='multipart/form-data', follow_redirects=True)
        assert edit_resp2.status_code == 200

        with app.app_context():
            db.session.remove()
            p = Post.query.first()
            assert p.featured_image is not None
            second_path = os.path.join(app.root_path, p.featured_image.lstrip('/'))
            assert os.path.exists(second_path)

        # Delete post
        del_resp = client.post('/post/delete/1', follow_redirects=True)
        assert del_resp.status_code == 200

        # Verify post is removed and image file is deleted
        with app.app_context():
            db.session.remove()
            assert Post.query.get(1) is None
            assert not os.path.exists(second_path), "Featured image file was not deleted from disk on post removal"
        print("Delete post and active cover image file cleanup verification passed successfully.")

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
        test_image_upload_and_processing()
        print("\nAll image upload & processing checks passed successfully!")
    except AssertionError as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
