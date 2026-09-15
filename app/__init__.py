import os
from flask import Flask
from dotenv import load_dotenv
from flask_login import LoginManager
from app.models import db, User

# Load environment variables from .env
load_dotenv()

def create_app():
    # Set templates and static folder paths relative to this file
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'views'))
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

    # App configurations
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev_key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///blog.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Upload folder configuration
    app.config['UPLOAD_FOLDER'] = os.path.join(static_dir, 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize extensions
    db.init_app(app)

    from flask_wtf.csrf import CSRFProtect
    csrf = CSRFProtect()
    csrf.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Custom Jinja2 Filters
    @app.template_filter('strftime')
    def _jinja2_filter_datetime(date, fmt=None):
        if not date:
            return ""
        # Apply standard format if none provided
        if fmt is None:
            fmt = '%b %d, %Y'
        return date.strftime(fmt)

    # Register blueprints (Controllers)
    from app.controllers.auth import auth_bp
    from app.controllers.blog import blog_bp
    from app.controllers.ai import ai_bp
    from app.controllers.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(blog_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(admin_bp)

    # Request Entity Too Large (413) Error Handler
    from werkzeug.exceptions import RequestEntityTooLarge
    from flask import flash, redirect, url_for, request

    @app.errorhandler(413)
    @app.errorhandler(RequestEntityTooLarge)
    def handle_request_entity_too_large(error):
        flash("The uploaded file is too large. Maximum size allowed is 16MB.", "danger")
        return redirect(request.referrer or url_for('blog.index'))

    @app.errorhandler(404)
    def page_not_found(error):
        from flask import render_template
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        from flask import render_template
        return render_template('errors/500.html'), 500

    return app
