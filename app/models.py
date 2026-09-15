from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import re

db = SQLAlchemy()

# Association table for Many-to-Many relationship between Post and Tag
post_tags = db.Table('post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('posts.id', ondelete='CASCADE'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    bio = db.Column(db.String(200), nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    posts = db.relationship('Post', backref='author', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='author', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_avatar(self):
        """Returns the user's avatar URL or a default offline-safe base64 SVG avatar."""
        if self.avatar_url:
            return self.avatar_url
        
        import base64
        svg_index = sum(ord(c) for c in self.username) % 5 if self.username else 0
        
        avatars = [
            # 1. Cyberpunk Neon Robot
            ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
             '<rect width="100" height="100" rx="20" fill="#0b0f19"/>'
             '<polygon points="50,15 80,32.5 80,67.5 50,85 20,67.5 20,32.5" fill="none" stroke="#6366f1" stroke-width="2" opacity="0.3"/>'
             '<rect x="30" y="35" width="40" height="30" rx="8" fill="#1f2937" stroke="#6366f1" stroke-width="3"/>'
             '<line x1="25" y1="50" x2="30" y2="50" stroke="#a855f7" stroke-width="4" stroke-linecap="round"/>'
             '<line x1="70" y1="50" x2="75" y2="50" stroke="#a855f7" stroke-width="4" stroke-linecap="round"/>'
             '<line x1="50" y1="25" x2="50" y2="35" stroke="#6366f1" stroke-width="3"/>'
             '<circle cx="50" cy="22" r="4" fill="#06b6d4"/>'
             '<circle cx="42" cy="50" r="5" fill="#06b6d4"/>'
             '<circle cx="58" cy="50" r="5" fill="#06b6d4"/>'
             '<path d="M 40 58 Q 50 62 60 58" stroke="#a855f7" stroke-width="2" fill="none"/>'
             '</svg>'),
            
            # 2. Sci-Fi Space Helmet/Astronaut
            ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
             '<rect width="100" height="100" rx="20" fill="#0f172a"/>'
             '<circle cx="25" cy="25" r="1.5" fill="#ffffff" opacity="0.8"/>'
             '<circle cx="75" cy="30" r="1" fill="#ffffff" opacity="0.5"/>'
             '<circle cx="35" cy="70" r="1.2" fill="#ffffff" opacity="0.6"/>'
             '<circle cx="50" cy="50" r="28" fill="#e2e8f0" stroke="#475569" stroke-width="2"/>'
             '<path d="M 28 48 Q 50 35 72 48 Q 70 70 50 70 Q 30 70 28 48 Z" fill="url(#visorGrad)" stroke="#3b82f6" stroke-width="2"/>'
             '<defs>'
             '<linearGradient id="visorGrad" x1="0%" y1="0%" x2="100%" y2="100%">'
             '<stop offset="0%" stop-color="#2563eb"/>'
             '<stop offset="50%" stop-color="#a855f7"/>'
             '<stop offset="100%" stop-color="#db2777"/>'
             '</linearGradient>'
             '</defs>'
             '<path d="M 33 46 Q 50 38 67 46" stroke="#ffffff" stroke-width="2" fill="none" opacity="0.5"/>'
             '</svg>'),
            
            # 3. Retro Game Controller / Pixel Art Invader
            ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
             '<rect width="100" height="100" rx="20" fill="#050505"/>'
             '<path d="M 30 30 h 8 v 8 h -8 z M 62 30 h 8 v 8 h -8 z M 38 38 h 24 v 8 h -24 z M 30 46 h 40 v 8 h -40 z M 30 54 h 8 v 8 h -8 z M 46 54 h 8 v 8 h -8 z M 62 54 h 8 v 8 h -8 z M 22 62 h 8 v 8 h -8 z M 70 62 h 8 v 8 h -8 z" fill="#10b981"/>'
             '<line x1="0" y1="80" x2="100" y2="80" stroke="#f43f5e" stroke-width="1.5" opacity="0.4"/>'
             '<line x1="0" y1="90" x2="100" y2="90" stroke="#f43f5e" stroke-width="1.5" opacity="0.2"/>'
             '</svg>'),
            
            # 4. Code Bracket Glowing Shield
            ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
             '<rect width="100" height="100" rx="20" fill="#080711"/>'
             '<path d="M 30 25 Q 50 20 70 25 Q 70 55 50 78 Q 30 55 30 25 Z" fill="none" stroke="#f59e0b" stroke-width="3"/>'
             '<text x="50" y="55" font-family="Courier New, monospace" font-weight="900" font-size="32" fill="#ffffff" text-anchor="middle" dominant-baseline="middle">&lt;/&gt;</text>'
             '</svg>'),
            
            # 5. Tech Chip / Processor
            ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
             '<rect width="100" height="100" rx="20" fill="#0c101d"/>'
             '<path d="M 50 10 L 50 30 M 50 90 L 50 70 M 10 50 L 30 50 M 90 50 L 70 50 M 20 20 L 35 35 M 80 80 L 65 65 M 80 20 L 65 35 M 20 80 L 35 65" stroke="#06b6d4" stroke-width="2" opacity="0.4"/>'
             '<rect x="32" y="32" width="36" height="36" rx="6" fill="#1e293b" stroke="#06b6d4" stroke-width="3"/>'
             '<circle cx="50" cy="50" r="8" fill="#a855f7"/>'
             '</svg>')
        ]
        
        svg = avatars[svg_index]
        encoded = base64.b64encode(svg.encode('utf-8')).decode('utf-8')
        return f"data:image/svg+xml;base64,{encoded}"

    def __repr__(self):
        return f"<User {self.username}>"

class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False, index=True)

    # Relationships
    posts = db.relationship('Post', backref='category', lazy=True)

    @staticmethod
    def generate_slug(name):
        """Generates a URL-friendly slug from name."""
        slug = name.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'[\s-]+', '-', slug)
        return slug.strip('-')

    def __repr__(self):
        return f"<Category {self.name}>"

class Post(db.Model):
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.String(300), nullable=True)
    featured_image = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default='Published', nullable=False) # 'Published' or 'Draft'
    is_featured = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Foreign Keys
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    # Relationships
    comments = db.relationship('Comment', backref='post', lazy=True, cascade='all, delete-orphan')
    tags = db.relationship('Tag', secondary=post_tags, backref=db.backref('posts', lazy='dynamic'))

    @staticmethod
    def generate_slug(title):
        """Generates a URL-friendly slug from title."""
        slug = title.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'[\s-]+', '-', slug)
        return slug.strip('-')

    def __repr__(self):
        return f"<Post {self.title}>"

class Tag(db.Model):
    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True, nullable=False, index=True)

    def __repr__(self):
        return f"<Tag {self.name}>"

class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Foreign Keys
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    def __repr__(self):
        return f"<Comment {self.id} on Post {self.post_id}>"

class Banner(db.Model):
    __tablename__ = 'banners'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    subtitle = db.Column(db.String(200), nullable=True)
    image_url = db.Column(db.String(255), nullable=False)
    link_url = db.Column(db.String(255), nullable=True)
    button_text = db.Column(db.String(50), nullable=True)
    display_order = db.Column(db.Integer, default=0, nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Banner {self.title}>"

class ContactMessage(db.Model):
    __tablename__ = 'contact_messages'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<ContactMessage {self.subject} from {self.name}>"

class NewsletterSubscriber(db.Model):
    __tablename__ = 'newsletter_subscribers'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<NewsletterSubscriber {self.email}>"

class AboutPage(db.Model):
    __tablename__ = 'about_pages'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    mission = db.Column(db.Text, nullable=False)
    vision = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<AboutPage {self.title}>"

class TeamMember(db.Model):
    __tablename__ = 'team_members'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    avatar = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.String(255), nullable=True)
    display_order = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<TeamMember {self.name} - {self.role}>"
