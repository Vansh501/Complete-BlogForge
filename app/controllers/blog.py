import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify, current_app
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from app.models import db, Post, Tag, Comment, User, Category, Banner, ContactMessage, NewsletterSubscriber, AboutPage, TeamMember
import uuid
from app.utils.image import save_and_resize_image, delete_old_image
from app.utils.ai_suggestions import get_ai_post_suggestions, get_ai_suggested_topics

blog_bp = Blueprint('blog', __name__)

@blog_bp.context_processor
def inject_user_posts_status():
    if current_user.is_authenticated:
        user_posts_count = Post.query.filter_by(author_id=current_user.id).count()
        has_no_posts = (user_posts_count == 0)
        
        suggested_topics = []
        if has_no_posts:
            suggested_topics = get_ai_suggested_topics()
            
        return {
            'has_no_posts': has_no_posts,
            'suggested_topics': suggested_topics
        }
    return {
        'has_no_posts': False,
        'suggested_topics': []
    }

@blog_bp.route('/')
def index():
    if not current_user.is_authenticated:
        return render_template('blog/landing.html')

    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('q', '').strip()
    tag_name = request.args.get('tag', '').strip()
    category_slug = request.args.get('category', '').strip()
    author_username = request.args.get('author', '').strip()
    sort_by = request.args.get('sort', 'newest').strip().lower()

    # Base query for published posts filtered by current user
    posts_query = Post.query.filter_by(status='Published', author_id=current_user.id)

    if search_query:
        # Search by post title, content, author username, category name, or tag name
        posts_query = posts_query.outerjoin(User, Post.author_id == User.id)\
                                 .outerjoin(Category, Post.category_id == Category.id)\
                                 .outerjoin(Post.tags)\
                                 .filter(
                                     (Post.title.ilike(f'%{search_query}%')) |
                                     (Post.content.ilike(f'%{search_query}%')) |
                                     (User.username.ilike(f'%{search_query}%')) |
                                     (Category.name.ilike(f'%{search_query}%')) |
                                     (Tag.name.ilike(f'%{search_query}%'))
                                 ).distinct()

    if tag_name:
        # Filter posts by tag
        posts_query = posts_query.join(Post.tags).filter(Tag.name.ilike(tag_name))

    if category_slug:
        # Filter posts by category
        posts_query = posts_query.join(Category).filter(Category.slug == category_slug)

    if author_username:
        # Filter posts by author
        posts_query = posts_query.join(User, Post.author_id == User.id).filter(User.username == author_username)

    # Fetch featured posts
    featured_posts = []
    total_featured_count = Post.query.filter_by(status='Published', is_featured=True, author_id=current_user.id).count()
    if page == 1 and not search_query and not tag_name and not category_slug and not author_username:
        featured_posts = Post.query.filter_by(status='Published', is_featured=True, author_id=current_user.id).order_by(Post.created_at.desc()).limit(3).all()
        featured_ids = [p.id for p in featured_posts]
        if featured_ids:
            posts_query = posts_query.filter(Post.id.notin_(featured_ids))

    # Apply sorting
    if sort_by == 'oldest':
        order_expr = Post.created_at.asc()
    elif sort_by == 'title_asc':
        order_expr = Post.title.asc()
    elif sort_by == 'title_desc':
        order_expr = Post.title.desc()
    else:
        order_expr = Post.created_at.desc()

    is_homepage_default = not search_query and not tag_name and not category_slug and not author_username
    per_page_limit = 3 if is_homepage_default else 6

    # Paginate posts
    pagination = posts_query.order_by(order_expr).paginate(
        page=page, per_page=per_page_limit, error_out=False
    )
    posts = pagination.items

    # Fetch all tags with their count for sidebar
    all_tags = Tag.query.all()
    tag_counts = []
    for tag in all_tags:
        count = tag.posts.filter(Post.status == 'Published', Post.author_id == current_user.id).count()
        if count > 0:
            tag_counts.append((tag, count))
    tag_counts.sort(key=lambda x: x[1], reverse=True)
    popular_tags = tag_counts[:10]  # Show top 10 tags

    # Fetch all categories with post counts
    all_categories = Category.query.all()
    categories_with_count = []
    for cat in all_categories:
        count = Post.query.filter_by(category_id=cat.id, status='Published', author_id=current_user.id).count()
        categories_with_count.append((cat, count))

    # Fetch active banners for top carousel sorted by display order
    banners = Banner.query.filter_by(active=True).order_by(Banner.display_order.asc(), Banner.created_at.desc()).all()

    # Fetch recent posts
    recent_posts = Post.query.filter_by(status='Published', author_id=current_user.id).order_by(Post.created_at.desc()).limit(5).all()

    # Find the current category if slug is active
    selected_category = Category.query.filter_by(slug=category_slug).first() if category_slug else None

    # Fetch AI suggestions for new users who have 0 posts
    ai_suggestions = []
    if Post.query.filter_by(author_id=current_user.id).count() == 0:
        ai_suggestions = get_ai_post_suggestions(current_user.id)

    return render_template(
        'blog/index.html',
        posts=posts,
        featured_posts=featured_posts,
        total_featured_count=total_featured_count,
        is_homepage_default=is_homepage_default,
        pagination=pagination,
        search_query=search_query,
        selected_tag=tag_name,
        selected_category=selected_category,
        selected_author=author_username,
        ai_suggestions=ai_suggestions,
        categories=categories_with_count,
        popular_tags=popular_tags,
        recent_posts=recent_posts,
        banners=banners,
        selected_sort=sort_by
    )

@blog_bp.route('/featured')
def featured_posts():
    if not current_user.is_authenticated:
        flash('Please log in to view featured articles.', 'warning')
        return redirect(url_for('blog.index'))
    
    page = request.args.get('page', 1, type=int)
    posts_query = Post.query.filter_by(status='Published', is_featured=True).order_by(Post.created_at.desc())
    
    pagination = posts_query.paginate(page=page, per_page=6, error_out=False)
    posts = pagination.items
    
    # Fetch sidebar widgets data
    all_tags = Tag.query.all()
    tag_counts = []
    for t in all_tags:
        count = t.posts.filter(Post.status == 'Published').count()
        if count > 0:
            tag_counts.append((t, count))
    tag_counts.sort(key=lambda x: x[1], reverse=True)
    popular_tags = tag_counts[:10]

    all_categories = Category.query.all()
    categories_with_count = []
    for cat in all_categories:
        count = Post.query.filter_by(category_id=cat.id, status='Published').count()
        categories_with_count.append((cat, count))
        
    recent_posts = Post.query.filter_by(status='Published').order_by(Post.created_at.desc()).limit(5).all()

    return render_template(
        'blog/featured_posts.html',
        posts=posts,
        pagination=pagination,
        categories=categories_with_count,
        popular_tags=popular_tags,
        recent_posts=recent_posts
    )

@blog_bp.route('/post/<slug>')
def post_detail(slug):
    if not current_user.is_authenticated:
        flash('Please log in to read this article.', 'warning')
        return redirect(url_for('blog.index'))

    post = Post.query.filter_by(slug=slug).first_or_404()
    
    # If draft, only allow author to view it
    if post.status == 'Draft':
        if not current_user.is_authenticated or current_user.id != post.author_id:
            abort(403)

    # Fetch previous and next post
    prev_post = Post.query.filter(Post.status == 'Published', Post.created_at < post.created_at).order_by(Post.created_at.desc()).first()
    next_post = Post.query.filter(Post.status == 'Published', Post.created_at > post.created_at).order_by(Post.created_at.asc()).first()

    # Fetch related posts (same category first, fallback to latest, excluding current post)
    related_posts = Post.query.filter(Post.status == 'Published', Post.category_id == post.category_id, Post.id != post.id).order_by(Post.created_at.desc()).limit(3).all()
    if len(related_posts) < 3:
        already_selected = [p.id for p in related_posts] + [post.id]
        extra_posts = Post.query.filter(Post.status == 'Published', Post.id.notin_(already_selected)).order_by(Post.created_at.desc()).limit(3 - len(related_posts)).all()
        related_posts.extend(extra_posts)

    return render_template(
        'blog/post.html',
        post=post,
        prev_post=prev_post,
        next_post=next_post,
        related_posts=related_posts
    )

@blog_bp.route('/category/<slug>')
def category_detail(slug):
    if not current_user.is_authenticated:
        flash('Please log in to browse categories.', 'warning')
        return redirect(url_for('blog.index'))

    category = Category.query.filter_by(slug=slug).first_or_404()
    page = request.args.get('page', 1, type=int)
    
    # Query posts under this category
    posts_query = Post.query.filter_by(category_id=category.id, status='Published')
    
    # Paginate posts (6 per page)
    pagination = posts_query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=6, error_out=False
    )
    posts = pagination.items
    
    # Fetch tag cloud data for sidebar
    all_tags = Tag.query.all()
    tag_counts = []
    for tag in all_tags:
        count = tag.posts.filter(Post.status == 'Published').count()
        if count > 0:
            tag_counts.append((tag, count))
    tag_counts.sort(key=lambda x: x[1], reverse=True)
    popular_tags = tag_counts[:10]

    # Fetch categories for sidebar
    all_categories = Category.query.all()
    categories_with_count = []
    for cat in all_categories:
        count = Post.query.filter_by(category_id=cat.id, status='Published').count()
        categories_with_count.append((cat, count))

    # Fetch recent posts for sidebar
    recent_posts = Post.query.filter_by(status='Published').order_by(Post.created_at.desc()).limit(5).all()

    return render_template(
        'blog/category_posts.html',
        category=category,
        posts=posts,
        pagination=pagination,
        categories=categories_with_count,
        popular_tags=popular_tags,
        recent_posts=recent_posts
    )

@blog_bp.route('/tag/<name>')
def tag_detail(name):
    if not current_user.is_authenticated:
        flash('Please log in to browse tags.', 'warning')
        return redirect(url_for('blog.index'))

    tag = Tag.query.filter_by(name=name).first_or_404()
    page = request.args.get('page', 1, type=int)
    
    # Query posts under this tag
    posts_query = Post.query.join(Post.tags).filter(Tag.id == tag.id, Post.status == 'Published')
    
    # Paginate posts (6 per page)
    pagination = posts_query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=6, error_out=False
    )
    posts = pagination.items
    
    # Fetch tag cloud data for sidebar
    all_tags = Tag.query.all()
    tag_counts = []
    for t in all_tags:
        count = t.posts.filter(Post.status == 'Published').count()
        if count > 0:
            tag_counts.append((t, count))
    tag_counts.sort(key=lambda x: x[1], reverse=True)
    popular_tags = tag_counts[:10]

    # Fetch categories for sidebar
    all_categories = Category.query.all()
    categories_with_count = []
    for cat in all_categories:
        count = Post.query.filter_by(category_id=cat.id, status='Published').count()
        categories_with_count.append((cat, count))

    # Fetch recent posts for sidebar
    recent_posts = Post.query.filter_by(status='Published').order_by(Post.created_at.desc()).limit(5).all()

    return render_template(
        'blog/tag_posts.html',
        tag=tag,
        posts=posts,
        pagination=pagination,
        categories=categories_with_count,
        popular_tags=popular_tags,
        recent_posts=recent_posts
    )

@blog_bp.route('/about')
def about():
    about_data = AboutPage.query.first()
    team_members = TeamMember.query.order_by(TeamMember.display_order.asc(), TeamMember.created_at.desc()).all()
    return render_template('blog/about.html', about=about_data, team_members=team_members)

@blog_bp.route('/post/create', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        summary = request.form.get('summary', '').strip()
        featured_image = None

        # Handle file upload
        file = request.files.get('featured_image_file')
        if file and file.filename != '':
            featured_image = save_and_resize_image(file, 'posts')
            if not featured_image:
                flash('Invalid image format or failed to save.', 'danger')
                categories = Category.query.all()
                return render_template('blog/editor.html', post=None, categories=categories)
        category_id = request.form.get('category_id')
        status = request.form.get('status', 'Published') # 'Published' or 'Draft'
        is_featured = request.form.get('is_featured') in ['true', 'on']
        tags_input = request.form.get('tags', '').strip()

        if not title or not content:
            flash('Title and content are required fields.', 'danger')
            categories = Category.query.all()
            return render_template('blog/editor.html', post=None, categories=categories)

        # Generate a unique slug
        base_slug = Post.generate_slug(title)
        slug = base_slug
        while Post.query.filter_by(slug=slug).first() is not None:
            slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"

        new_post = Post(
            title=title,
            content=content,
            slug=slug,
            summary=summary if summary else (content[:150] + '...' if len(content) > 150 else content),
            featured_image=featured_image if featured_image else None,
            category_id=int(category_id) if category_id and category_id.isdigit() else None,
            status=status,
            is_featured=is_featured,
            author_id=current_user.id
        )
        db.session.add(new_post)

        # Process tags
        if tags_input:
            tag_names = [name.strip().lower() for name in tags_input.split(',') if name.strip()]
            for name in set(tag_names):
                tag = Tag.query.filter_by(name=name).first()
                if not tag:
                    tag = Tag(name=name)
                    db.session.add(tag)
                new_post.tags.append(tag)

        try:
            db.session.commit()
            flash(f'Post "{title}" created successfully!', 'success')
            return redirect(url_for('blog.post_detail', slug=new_post.slug))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating the post. Please try again.', 'danger')

    categories = Category.query.all()
    prefill_title = request.args.get('title', '').strip()
    prefill_content = request.args.get('content', '').strip()
    prefill_category = request.args.get('category', '').strip()
    return render_template(
        'blog/editor.html', 
        post=None, 
        categories=categories,
        prefill_title=prefill_title,
        prefill_content=prefill_content,
        prefill_category=prefill_category
    )

@blog_bp.route('/post/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    post = Post.query.get_or_404(id)

    # Authorization check
    if post.author_id != current_user.id:
        abort(403)

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        summary = request.form.get('summary', '').strip()
        # Check if remove image is selected
        old_image = post.featured_image
        if request.form.get('clear_featured_image') == 'true':
            featured_image = None
            if old_image:
                delete_old_image(old_image)
        else:
            featured_image = post.featured_image

        # Handle file upload
        file = request.files.get('featured_image_file')
        if file and file.filename != '':
            new_image = save_and_resize_image(file, 'posts')
            if new_image:
                featured_image = new_image
                if old_image:
                    delete_old_image(old_image)
            else:
                flash('Invalid image format or failed to save.', 'danger')
                categories = Category.query.all()
                post_tags_str = ", ".join([tag.name for tag in post.tags])
                return render_template('blog/editor.html', post=post, tags_str=post_tags_str, categories=categories)
        category_id = request.form.get('category_id')
        status = request.form.get('status', 'Published')
        is_featured = request.form.get('is_featured') in ['true', 'on']
        tags_input = request.form.get('tags', '').strip()

        if not title or not content:
            flash('Title and content are required fields.', 'danger')
            categories = Category.query.all()
            post_tags_str = ", ".join([tag.name for tag in post.tags])
            return render_template('blog/editor.html', post=post, tags_str=post_tags_str, categories=categories)

        # Update slug if title changes
        if post.title != title:
            base_slug = Post.generate_slug(title)
            slug = base_slug
            while Post.query.filter(Post.slug == slug, Post.id != id).first() is not None:
                slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"
            post.slug = slug

        post.title = title
        post.content = content
        post.summary = summary if summary else (content[:150] + '...' if len(content) > 150 else content)
        post.featured_image = featured_image if featured_image else None
        post.category_id = int(category_id) if category_id and category_id.isdigit() else None
        post.status = status
        post.is_featured = is_featured

        # Update Tags
        post.tags.clear()
        if tags_input:
            tag_names = [name.strip().lower() for name in tags_input.split(',') if name.strip()]
            for name in set(tag_names):
                tag = Tag.query.filter_by(name=name).first()
                if not tag:
                    tag = Tag(name=name)
                    db.session.add(tag)
                post.tags.append(tag)

        try:
            db.session.commit()
            flash(f'Post "{title}" updated successfully!', 'success')
            return redirect(url_for('blog.post_detail', slug=post.slug))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the post.', 'danger')

    categories = Category.query.all()
    post_tags_str = ", ".join([tag.name for tag in post.tags])
    return render_template('blog/editor.html', post=post, tags_str=post_tags_str, categories=categories)

@blog_bp.route('/post/delete/<int:id>', methods=['POST'])
@login_required
def delete_post(id):
    post = Post.query.get_or_404(id)

    # Authorization check
    if post.author_id != current_user.id:
        abort(403)

    try:
        old_image = post.featured_image
        db.session.delete(post)
        db.session.commit()
        if old_image:
            delete_old_image(old_image)
        flash('Post deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the post.', 'danger')

    return redirect(url_for('blog.index'))

@blog_bp.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    content = request.form.get('content', '').strip()

    if not content:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'Comment content cannot be empty.'}), 400
        flash('Comment cannot be empty.', 'danger')
        return redirect(url_for('blog.post_detail', slug=post.slug))

    new_comment = Comment(
        content=content,
        post_id=post_id,
        user_id=current_user.id
    )

    try:
        db.session.add(new_comment)
        db.session.commit()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'comment': {
                    'author': current_user.username,
                    'avatar_url': current_user.get_avatar(),
                    'content': new_comment.content,
                    'created_at': new_comment.created_at.strftime('%b %d, %Y at %H:%M')
                }
            })

        flash('Comment added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'Failed to save comment.'}), 500
        flash('Failed to post comment. Please try again.', 'danger')

    return redirect(url_for('blog.post_detail', slug=post.slug))

@blog_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()

        if not name or not email or not subject or not message:
            flash('All fields are required.', 'danger')
            return render_template('blog/contact.html')

        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            flash('Invalid email address format. Please enter a valid email.', 'danger')
            return render_template('blog/contact.html')

        new_message = ContactMessage(
            name=name,
            email=email,
            subject=subject,
            message=message
        )

        try:
            db.session.add(new_message)
            db.session.commit()
            flash('Your message has been sent successfully. We will get back to you soon!', 'success')
            return redirect(url_for('blog.index'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while sending your message. Please try again.', 'danger')

    return render_template('blog/contact.html')

@blog_bp.route('/newsletter/subscribe', methods=['POST'])
def newsletter_subscribe():
    email = request.form.get('email', '').strip()
    if not email:
        return jsonify({'error': 'Email address is required.'}), 400
    
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return jsonify({'error': 'Invalid email address format.'}), 400
    
    existing = NewsletterSubscriber.query.filter_by(email=email).first()
    if existing:
        return jsonify({'success': True, 'message': 'You are already subscribed to our newsletter!'})
    
    new_sub = NewsletterSubscriber(email=email)
    try:
        db.session.add(new_sub)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Thank you for subscribing to our newsletter!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to save subscription. Please try again.'}), 500

@blog_bp.route('/robots.txt')
def robots():
    response = current_app.make_response(f"User-agent: *\nAllow: /\nSitemap: {request.url_root}sitemap.xml\n")
    response.headers["Content-Type"] = "text/plain"
    return response

@blog_bp.route('/sitemap.xml')
def sitemap():
    from flask import make_response
    import xml.etree.ElementTree as ET
    from app.models import Post, Category, Tag
    
    root = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    
    # 1. Main Static pages
    static_urls = [
        url_for('blog.index'),
        url_for('blog.about'),
        url_for('blog.contact')
    ]
    for url in static_urls:
        url_el = ET.SubElement(root, "url")
        loc = ET.SubElement(url_el, "loc")
        loc.text = f"{request.url_root.rstrip('/')}{url}"
        changefreq = ET.SubElement(url_el, "changefreq")
        changefreq.text = "daily"
        priority = ET.SubElement(url_el, "priority")
        priority.text = "1.0"
        
    # 2. Published Posts
    posts = Post.query.filter_by(status='Published').order_by(Post.updated_at.desc()).all()
    for post in posts:
        url_el = ET.SubElement(root, "url")
        loc = ET.SubElement(url_el, "loc")
        loc.text = f"{request.url_root.rstrip('/')}{url_for('blog.post_detail', slug=post.slug)}"
        lastmod = ET.SubElement(url_el, "lastmod")
        lastmod.text = post.updated_at.strftime('%Y-%m-%d')
        changefreq = ET.SubElement(url_el, "changefreq")
        changefreq.text = "weekly"
        priority = ET.SubElement(url_el, "priority")
        priority.text = "0.8"
        
    # 3. Categories
    categories = Category.query.all()
    for cat in categories:
        url_el = ET.SubElement(root, "url")
        loc = ET.SubElement(url_el, "loc")
        loc.text = f"{request.url_root.rstrip('/')}{url_for('blog.category_detail', slug=cat.slug)}"
        changefreq = ET.SubElement(url_el, "changefreq")
        changefreq.text = "weekly"
        priority = ET.SubElement(url_el, "priority")
        priority.text = "0.6"
        
    # 4. Tags
    tags = Tag.query.all()
    for tag in tags:
        url_el = ET.SubElement(root, "url")
        loc = ET.SubElement(url_el, "loc")
        loc.text = f"{request.url_root.rstrip('/')}{url_for('blog.tag_detail', name=tag.name)}"
        changefreq = ET.SubElement(url_el, "changefreq")
        changefreq.text = "weekly"
        priority = ET.SubElement(url_el, "priority")
        priority.text = "0.4"
        
    xml_string = ET.tostring(root, encoding='utf-8', method='xml')
    response = make_response(xml_string)
    response.headers["Content-Type"] = "application/xml"
    return response
