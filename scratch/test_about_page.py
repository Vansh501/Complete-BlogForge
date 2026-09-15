import os
import sys

# Ensure project root is in PYTHONPATH
sys.path.insert(0, r"c:\Users\ASUS\OneDrive\Desktop\blog-system")

from app import create_app
from app.models import db, TeamMember, AboutPage

def test_about_page_team_member():
    db_file = 'temp_test_about.db'
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

            # Seed About Page
            about = AboutPage(
                title='About Us',
                description='Welcome to AetherBlog',
                image_url='http://example.com/about.jpg',
                mission='To blog',
                vision='The future'
            )
            db.session.add(about)

            # Seed Team Member with name Clark
            member = TeamMember(
                name='Clark',
                role='FOUNDER & CORE DEV',
                bio='Lead architect and developer of AetherBlog.',
                display_order=1
            )
            db.session.add(member)
            db.session.commit()

        # Access About page
        resp = client.get('/about')
        assert resp.status_code == 200
        assert b'Clark' in resp.data
        assert b'Vansh Sharma' not in resp.data
        print("About page successfully displays Team Member Clark and hides Vansh Sharma.")

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
        test_about_page_team_member()
        print("\nAll about page verification tests passed successfully!")
    except AssertionError as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
