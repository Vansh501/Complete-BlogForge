import os
import sys
from io import BytesIO

# Ensure project root is in PYTHONPATH
sys.path.insert(0, r"c:\Users\ASUS\OneDrive\Desktop\blog-system")

from app import create_app
from app.models import db, User, Post

def test_user_profile_management():
    db_file = 'temp_test_profile.db'
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except Exception:
            pass

    os.environ['DATABASE_URL'] = f'sqlite:///{db_file}'
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'uploads')

    with app.test_client() as client:
        with app.app_context():
            db.drop_all()
            db.create_all()

            # Seed user
            u = User(username='test_user', email='test@user.com', bio='Original bio info.')
            u.set_password('oldpass123')
            db.session.add(u)
            db.session.commit()

            # Seed post A (Published) and post B (Draft)
            p_pub = Post(title='My First Article', slug='my-first-article', content='Flask is neat.', status='Published', author_id=u.id)
            p_dr = Post(title='Work in Progress', slug='work-in-progress', content='Draft flask.', status='Draft', author_id=u.id)
            db.session.add_all([p_pub, p_dr])
            db.session.commit()

        # 1. Access profile as anonymous visitor (must redirect)
        anon_resp = client.get('/profile')
        assert anon_resp.status_code == 302
        assert '/login' in anon_resp.location
        print("Anonymous profile redirection check passed.")

        # 2. Log in
        login_resp = client.post('/login', data={'login_credential': 'test_user', 'password': 'oldpass123'})
        assert login_resp.status_code == 302

        # 3. Access profile and check fields
        prof_resp = client.get('/profile')
        assert prof_resp.status_code == 200
        assert b'test_user' in prof_resp.data
        assert b'test@user.com' in prof_resp.data
        assert b'My First Article' in prof_resp.data
        assert b'Work in Progress' in prof_resp.data
        print("Logged in profile loading and list tabs verified successfully.")

        # 4. Update information (with avatar upload)
        avatar_file = (BytesIO(b"user avatar image"), "test_avatar.png")
        data_info = {
            'action': 'update_info',
            'username': 'new_username',
            'email': 'new@email.com',
            'bio': 'My updated bio description.',
            'avatar_file': avatar_file
        }
        update_info_resp = client.post('/profile', data=data_info, content_type='multipart/form-data', follow_redirects=True)
        assert update_info_resp.status_code == 200
        assert b'information updated successfully' in update_info_resp.data or b'Profile information updated successfully' in update_info_resp.data

        # Verify DB updates
        with app.app_context():
            db.session.remove()
            updated_u = User.query.first()
            assert updated_u.username == 'new_username'
            assert updated_u.email == 'new@email.com'
            assert updated_u.bio == 'My updated bio description.'
            assert updated_u.avatar_url.startswith('/static/uploads/avatars/')
        print("Profile information update (including photo upload) verified successfully.")

        # 5. Change Password
        data_pass = {
            'action': 'change_password',
            'current_password': 'oldpass123',
            'new_password': 'newpassword456',
            'confirm_password': 'newpassword456'
        }
        update_pass_resp = client.post('/profile', data=data_pass, follow_redirects=True)
        assert update_pass_resp.status_code == 200
        assert b'Password changed successfully' in update_pass_resp.data

        # Verify password logic by logging in again
        logout_resp = client.get('/logout', follow_redirects=True)
        assert logout_resp.status_code == 200

        login_again_resp = client.post('/login', data={'login_credential': 'new_username', 'password': 'newpassword456'}, follow_redirects=True)
        assert login_again_resp.status_code == 200
        assert b'Welcome back' in login_again_resp.data
        print("Change password and login update verified successfully.")

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
        test_user_profile_management()
        print("\nAll user profile management checks passed successfully!")
    except AssertionError as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
