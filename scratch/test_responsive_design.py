import os
import sys

# Ensure project root is in PYTHONPATH
sys.path.insert(0, r"c:\Users\ASUS\OneDrive\Desktop\blog-system")

from app import create_app

def test_responsive_meta_and_css():
    app = create_app()
    app.config['TESTING'] = True

    with app.test_client() as client:
        # 1. Fetch homepage and verify viewport meta tag is present
        resp = client.get('/')
        assert resp.status_code == 200
        assert b'<meta name="viewport" content="width=device-width, initial-scale=1.0">' in resp.data
        print("Viewport meta tag check passed.")

        # 2. Fetch style.css and verify custom media queries are present
        css_resp = client.get('/static/css/style.css')
        assert css_resp.status_code == 200
        assert b'@media (max-width: 991.98px)' in css_resp.data
        assert b'@media (max-width: 575.98px)' in css_resp.data
        print("CSS media queries for Mobile and Tablet scaling checked successfully.")

if __name__ == '__main__':
    try:
        test_responsive_meta_and_css()
        print("\nAll responsive design checks passed successfully!")
    except AssertionError as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
