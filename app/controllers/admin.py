from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.models import db, User, Post, Category, Tag, Banner, ContactMessage, AboutPage, TeamMember
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Statistics calculations
    total_posts = Post.query.count()
    published_posts = Post.query.filter_by(status='Published').count()
    draft_posts = Post.query.filter_by(status='Draft').count()
    total_categories = Category.query.count()
    total_users = User.query.count()
    total_banners = Banner.query.count()
    total_messages = ContactMessage.query.count()

    # Recent items for overview
    recent_posts = Post.query.order_by(Post.created_at.desc()).limit(5).all()
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(5).all()

    return render_template(
        'admin/dashboard.html',
        stats={
            'total_posts': total_posts,
            'published_posts': published_posts,
            'draft_posts': draft_posts,
            'total_categories': total_categories,
            'total_users': total_users,
            'total_banners': total_banners,
            'total_messages': total_messages
        },
        recent_posts=recent_posts,
        recent_users=recent_users,
        recent_messages=recent_messages,
        active_tab='dashboard'
    )

@admin_bp.route('/posts')
@login_required
@admin_required
def manage_posts():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('admin/posts.html', posts=posts, active_tab='posts')

@admin_bp.route('/categories', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_categories():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Category name cannot be empty.', 'danger')
        else:
            slug = Category.generate_slug(name)
            if Category.query.filter_by(slug=slug).first():
                flash('A category with this name or slug already exists.', 'danger')
            else:
                new_cat = Category(name=name, slug=slug)
                db.session.add(new_cat)
                db.session.commit()
                flash(f'Category "{name}" added successfully.', 'success')
                return redirect(url_for('admin.manage_categories'))

    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories, active_tab='categories')

@admin_bp.route('/categories/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_category(id):
    cat = Category.query.get_or_404(id)
    try:
        # Posts belonging to this category will have category_id set to NULL due to SET NULL cascade
        db.session.delete(cat)
        db.session.commit()
        flash(f'Category "{cat.name}" deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the category.', 'danger')
    
    return redirect(url_for('admin.manage_categories'))

@admin_bp.route('/categories/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_category(id):
    cat = Category.query.get_or_404(id)
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Category name cannot be empty.', 'danger')
        else:
            slug = Category.generate_slug(name)
            existing = Category.query.filter(Category.slug == slug, Category.id != id).first()
            if existing:
                flash('A category with this name or slug already exists.', 'danger')
            else:
                cat.name = name
                cat.slug = slug
                try:
                    db.session.commit()
                    flash(f'Category updated to "{name}" successfully.', 'success')
                    return redirect(url_for('admin.manage_categories'))
                except Exception as e:
                    db.session.rollback()
                    flash('An error occurred while updating the category.', 'danger')
                    
    return render_template('admin/edit_category.html', category=cat, active_tab='categories')

@admin_bp.route('/banners', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_banners():
    import os
    import uuid
    from werkzeug.utils import secure_filename
    from flask import current_app

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        subtitle = request.form.get('subtitle', '').strip()
        link_url = request.form.get('link_url', '').strip()
        button_text = request.form.get('button_text', '').strip()
        display_order_str = request.form.get('display_order', '0').strip()
        active = True if request.form.get('active') else False

        try:
            display_order = int(display_order_str)
        except ValueError:
            display_order = 0

        # Handle image file upload
        image_url = None
        file = request.files.get('banner_image_file')
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            ext = os.path.splitext(filename)[1].lower()
            if ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
                # Save under static/uploads/banners
                banners_upload_dir = os.path.join(current_app.static_folder, 'uploads', 'banners')
                os.makedirs(banners_upload_dir, exist_ok=True)
                unique_filename = f"{uuid.uuid4().hex}{ext}"
                try:
                    file.save(os.path.join(banners_upload_dir, unique_filename))
                    image_url = f"/static/uploads/banners/{unique_filename}"
                except Exception as e:
                    flash('Failed to save uploaded image.', 'danger')
            else:
                flash('Invalid image format. Allowed: PNG, JPG, JPEG, GIF, WEBP.', 'danger')
        
        if not title:
            flash('Banner title is required.', 'danger')
        elif not image_url:
            flash('Banner image upload is required.', 'danger')
        else:
            new_banner = Banner(
                title=title,
                subtitle=subtitle if subtitle else None,
                image_url=image_url,
                link_url=link_url if link_url else None,
                button_text=button_text if button_text else None,
                display_order=display_order,
                active=active
            )
            db.session.add(new_banner)
            db.session.commit()
            flash(f'Banner "{title}" added successfully.', 'success')
            return redirect(url_for('admin.manage_banners'))

    banners = Banner.query.order_by(Banner.display_order.asc(), Banner.created_at.desc()).all()
    return render_template('admin/banners.html', banners=banners, active_tab='banners')

@admin_bp.route('/banners/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_banner(id):
    import os
    import uuid
    from werkzeug.utils import secure_filename
    from flask import current_app

    banner = Banner.query.get_or_404(id)
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        subtitle = request.form.get('subtitle', '').strip()
        link_url = request.form.get('link_url', '').strip()
        button_text = request.form.get('button_text', '').strip()
        display_order_str = request.form.get('display_order', '0').strip()
        active = True if request.form.get('active') else False

        try:
            display_order = int(display_order_str)
        except ValueError:
            display_order = 0

        # Handle image file upload (optional for editing)
        image_url = banner.image_url
        file = request.files.get('banner_image_file')
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            ext = os.path.splitext(filename)[1].lower()
            if ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
                # Save under static/uploads/banners
                banners_upload_dir = os.path.join(current_app.static_folder, 'uploads', 'banners')
                os.makedirs(banners_upload_dir, exist_ok=True)
                unique_filename = f"{uuid.uuid4().hex}{ext}"
                try:
                    file.save(os.path.join(banners_upload_dir, unique_filename))
                    image_url = f"/static/uploads/banners/{unique_filename}"
                except Exception as e:
                    flash('Failed to save uploaded image.', 'danger')
            else:
                flash('Invalid image format. Allowed: PNG, JPG, JPEG, GIF, WEBP.', 'danger')
        
        if not title:
            flash('Banner title is required.', 'danger')
        else:
            banner.title = title
            banner.subtitle = subtitle if subtitle else None
            banner.image_url = image_url
            banner.link_url = link_url if link_url else None
            banner.button_text = button_text if button_text else None
            banner.display_order = display_order
            banner.active = active
            
            try:
                db.session.commit()
                flash(f'Banner "{title}" updated successfully.', 'success')
                return redirect(url_for('admin.manage_banners'))
            except Exception as e:
                db.session.rollback()
                flash('An error occurred while updating the banner.', 'danger')

    return render_template('admin/edit_banner.html', banner=banner, active_tab='banners')

@admin_bp.route('/banners/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_banner(id):
    banner = Banner.query.get_or_404(id)
    try:
        db.session.delete(banner)
        db.session.commit()
        flash(f'Banner "{banner.title}" deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the banner.', 'danger')
    return redirect(url_for('admin.manage_banners'))

@admin_bp.route('/messages')
@login_required
@admin_required
def manage_messages():
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template('admin/messages.html', messages=messages, active_tab='messages')

@admin_bp.route('/messages/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_message(id):
    msg = ContactMessage.query.get_or_404(id)
    try:
        db.session.delete(msg)
        db.session.commit()
        flash(f'Message from "{msg.name}" deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the message.', 'danger')
    return redirect(url_for('admin.manage_messages'))

@admin_bp.route('/about', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_about():
    import os
    import uuid
    from werkzeug.utils import secure_filename
    from flask import current_app

    about_data = AboutPage.query.first()
    if about_data is None:
        about_data = AboutPage(
            title="About Us",
            description="Edit this description...",
            mission="Edit this mission...",
            vision="Edit this vision..."
        )
        db.session.add(about_data)
        db.session.commit()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        mission = request.form.get('mission', '').strip()
        vision = request.form.get('vision', '').strip()

        # Handle image file upload (optional)
        image_url = about_data.image_url
        file = request.files.get('about_image_file')
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            ext = os.path.splitext(filename)[1].lower()
            if ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
                upload_dir = os.path.join(current_app.static_folder, 'uploads', 'about')
                os.makedirs(upload_dir, exist_ok=True)
                unique_filename = f"{uuid.uuid4().hex}{ext}"
                try:
                    file.save(os.path.join(upload_dir, unique_filename))
                    image_url = f"/static/uploads/about/{unique_filename}"
                except Exception as e:
                    flash('Failed to save uploaded image.', 'danger')
            else:
                flash('Invalid image format. Allowed: PNG, JPG, JPEG, GIF, WEBP.', 'danger')

        if not title or not description:
            flash('About page title and description are required.', 'danger')
        else:
            about_data.title = title
            about_data.description = description
            about_data.image_url = image_url
            about_data.mission = mission
            about_data.vision = vision
            
            try:
                db.session.commit()
                flash('About page updated successfully.', 'success')
                return redirect(url_for('admin.manage_about'))
            except Exception as e:
                db.session.rollback()
                flash('An error occurred while updating the About page.', 'danger')

    team_members = TeamMember.query.order_by(TeamMember.display_order.asc(), TeamMember.created_at.desc()).all()
    return render_template('admin/about.html', about=about_data, team_members=team_members, active_tab='about')

@admin_bp.route('/team/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_team_member():
    import os
    import uuid
    from werkzeug.utils import secure_filename
    from flask import current_app

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        role = request.form.get('role', '').strip()
        bio = request.form.get('bio', '').strip()
        display_order_str = request.form.get('display_order', '0').strip()

        try:
            display_order = int(display_order_str)
        except ValueError:
            display_order = 0

        # Handle avatar file upload
        avatar = None
        file = request.files.get('avatar_file')
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            ext = os.path.splitext(filename)[1].lower()
            if ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
                upload_dir = os.path.join(current_app.static_folder, 'uploads', 'team')
                os.makedirs(upload_dir, exist_ok=True)
                unique_filename = f"{uuid.uuid4().hex}{ext}"
                try:
                    file.save(os.path.join(upload_dir, unique_filename))
                    avatar = f"/static/uploads/team/{unique_filename}"
                except Exception as e:
                    flash('Failed to save avatar image.', 'danger')
            else:
                flash('Invalid image format. Allowed: PNG, JPG, JPEG, GIF, WEBP.', 'danger')

        if not name or not role:
            flash('Name and role are required for team members.', 'danger')
        else:
            new_member = TeamMember(
                name=name,
                role=role,
                avatar=avatar,
                bio=bio if bio else None,
                display_order=display_order
            )
            db.session.add(new_member)
            db.session.commit()
            flash(f'Team member "{name}" added successfully.', 'success')
            return redirect(url_for('admin.manage_about'))

    return render_template('admin/edit_team.html', member=None, active_tab='about')

@admin_bp.route('/team/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_team_member(id):
    import os
    import uuid
    from werkzeug.utils import secure_filename
    from flask import current_app

    member = TeamMember.query.get_or_404(id)
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        role = request.form.get('role', '').strip()
        bio = request.form.get('bio', '').strip()
        display_order_str = request.form.get('display_order', '0').strip()

        try:
            display_order = int(display_order_str)
        except ValueError:
            display_order = 0

        # Handle avatar file upload
        avatar = member.avatar
        file = request.files.get('avatar_file')
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            ext = os.path.splitext(filename)[1].lower()
            if ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
                upload_dir = os.path.join(current_app.static_folder, 'uploads', 'team')
                os.makedirs(upload_dir, exist_ok=True)
                unique_filename = f"{uuid.uuid4().hex}{ext}"
                try:
                    file.save(os.path.join(upload_dir, unique_filename))
                    avatar = f"/static/uploads/team/{unique_filename}"
                except Exception as e:
                    flash('Failed to save avatar image.', 'danger')
            else:
                flash('Invalid image format. Allowed: PNG, JPG, JPEG, GIF, WEBP.', 'danger')

        if not name or not role:
            flash('Name and role are required.', 'danger')
        else:
            member.name = name
            member.role = role
            member.avatar = avatar
            member.bio = bio if bio else None
            member.display_order = display_order
            
            try:
                db.session.commit()
                flash(f'Team member "{name}" updated successfully.', 'success')
                return redirect(url_for('admin.manage_about'))
            except Exception as e:
                db.session.rollback()
                flash('An error occurred while updating the team member.', 'danger')

    return render_template('admin/edit_team.html', member=member, active_tab='about')

@admin_bp.route('/team/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_team_member(id):
    member = TeamMember.query.get_or_404(id)
    try:
        db.session.delete(member)
        db.session.commit()
        flash(f'Team member "{member.name}" deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the team member.', 'danger')
    return redirect(url_for('admin.manage_about'))
