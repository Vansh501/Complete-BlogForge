from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app.models import db, User
from urllib.parse import urlsplit

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('blog.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        bio = request.form.get('bio', '').strip()
        avatar_url = request.form.get('avatar_url', '').strip()

        # Validations
        if not username or not email or not password:
            flash('Username, email, and password are required.', 'danger')
            return render_template('auth/register.html')

        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            flash('Invalid email address format. Please enter a valid email.', 'danger')
            return render_template('auth/register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('auth/register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html')

        # Check existing user
        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose a different one.', 'danger')
            return render_template('auth/register.html')

        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please login instead.', 'danger')
            return render_template('auth/register.html')

        # Create new user
        new_user = User(
            username=username,
            email=email,
            bio=bio if bio else None,
            avatar_url=avatar_url if avatar_url else None
        )
        new_user.set_password(password)

        try:
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            flash('Registration successful! Welcome to the Blog Management System.', 'success')
            return redirect(url_for('blog.index'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'danger')

    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('blog.index'))

    if request.method == 'POST':
        login_credential = request.form.get('login_credential', '').strip() # Can be username or email
        password = request.form.get('password', '')
        remember = True if request.form.get('remember') else False

        if not login_credential or not password:
            flash('Please enter both your credentials and password.', 'danger')
            return render_template('auth/login.html')

        # Find user by username or email
        user = User.query.filter((User.username == login_credential) | (User.email == login_credential)).first()

        if not user or not user.check_password(password):
            flash('Invalid username/email or password. Please try again.', 'danger')
            return render_template('auth/login.html')

        # Login and redirect
        login_user(user, remember=remember)
        next_page = request.args.get('next')
        # Check against open redirect vulnerabilities
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('blog.index')
        
        flash(f'Welcome back, {user.username}!', 'success')
        return redirect(next_page)

    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('blog.index'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    import os
    import uuid
    from werkzeug.utils import secure_filename
    from flask import current_app
    from app.models import Post

    if request.method == 'POST':
        action = request.form.get('action') # 'update_info' or 'change_password'
        
        if action == 'update_info':
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            bio = request.form.get('bio', '').strip()
            
            # Check validations
            if not username or not email:
                flash('Username and email are required.', 'danger')
            else:
                # Check uniqueness of username and email
                exist_user = User.query.filter(User.id != current_user.id, User.username == username).first()
                exist_email = User.query.filter(User.id != current_user.id, User.email == email).first()
                
                if exist_user:
                    flash('Username is already taken.', 'danger')
                elif exist_email:
                    flash('Email address is already in use.', 'danger')
                else:
                    current_user.username = username
                    current_user.email = email
                    current_user.bio = bio if bio else None
                    
                    # Handle clear avatar
                    if request.form.get('clear_avatar') == 'true':
                        current_user.avatar_url = None
                    
                    # Handle preset avatar selection
                    preset = request.form.get('preset_avatar', '').strip()
                    if preset in ['avatar1', 'avatar2', 'avatar3', 'avatar4', 'avatar5']:
                        current_user.avatar_url = f"/static/images/{preset}.svg"
                    
                    # Handle avatar image upload
                    file = request.files.get('avatar_file')
                    if file and file.filename != '':
                        filename = secure_filename(file.filename)
                        ext = os.path.splitext(filename)[1].lower()
                        if ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
                            avatars_dir = os.path.join(current_app.static_folder, 'uploads', 'avatars')
                            os.makedirs(avatars_dir, exist_ok=True)
                            unique_filename = f"{uuid.uuid4().hex}{ext}"
                            try:
                                file.save(os.path.join(avatars_dir, unique_filename))
                                current_user.avatar_url = f"/static/uploads/avatars/{unique_filename}"
                            except Exception as e:
                                flash('Failed to save avatar image.', 'danger')
                        else:
                            flash('Invalid image format. Allowed: PNG, JPG, JPEG, GIF, WEBP.', 'danger')
                    
                    try:
                        db.session.commit()
                        flash('Profile information updated successfully.', 'success')
                    except Exception as e:
                        db.session.rollback()
                        flash('An error occurred while updating profile.', 'danger')
            return redirect(url_for('auth.profile'))
            
        elif action == 'change_password':
            current_pass = request.form.get('current_password', '')
            new_pass = request.form.get('new_password', '')
            confirm_pass = request.form.get('confirm_password', '')
            
            if not current_pass or not new_pass or not confirm_pass:
                flash('All password fields are required.', 'danger')
            elif not current_user.check_password(current_pass):
                flash('Incorrect current password.', 'danger')
            elif len(new_pass) < 6:
                flash('New password must be at least 6 characters long.', 'danger')
            elif new_pass != confirm_pass:
                flash('New passwords do not match.', 'danger')
            else:
                current_user.set_password(new_pass)
                try:
                    db.session.commit()
                    flash('Password changed successfully.', 'success')
                except Exception as e:
                    db.session.rollback()
                    flash('An error occurred while updating password.', 'danger')
            return redirect(url_for('auth.profile'))

    published_posts = Post.query.filter_by(author_id=current_user.id, status='Published').order_by(Post.created_at.desc()).all()
    draft_posts = Post.query.filter_by(author_id=current_user.id, status='Draft').order_by(Post.created_at.desc()).all()

    return render_template(
        'auth/profile.html',
        published_posts=published_posts,
        draft_posts=draft_posts
    )

@auth_bp.route('/profile/delete', methods=['POST'])
@login_required
def delete_account():
    user = User.query.get(current_user.id)
    logout_user()
    try:
        db.session.delete(user)
        db.session.commit()
        flash('Your account has been permanently deleted.', 'warning')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting your account.', 'danger')
    return redirect(url_for('blog.index'))
