from app import create_app
from app.models import db, User, Post, Tag, Category, Banner

app = create_app()


def seed_database():
    """Initializes tables and seeds default records if empty."""
    db.create_all()

    # Automatically add is_featured column if it doesn't exist (self-healing migration)
    try:
        db.session.execute(
            db.text(
                "ALTER TABLE posts ADD COLUMN is_featured BOOLEAN DEFAULT 0 NOT NULL"
            )
        )
        db.session.commit()
        print("Successfully added 'is_featured' column to posts table.")
    except Exception as e:
        db.session.rollback()
    # Automatically add button_text and display_order to banners if they don't exist
    try:
        db.session.execute(
            db.text("ALTER TABLE banners ADD COLUMN button_text VARCHAR(50)")
        )
        db.session.commit()
        print("Successfully added 'button_text' column to banners table.")
    except Exception as e:
        db.session.rollback()

    try:
        db.session.execute(
            db.text(
                "ALTER TABLE banners ADD COLUMN display_order INTEGER DEFAULT 0 NOT NULL"
            )
        )
        db.session.commit()
        print("Successfully added 'display_order' column to banners table.")
    except Exception as e:
        db.session.rollback()
    # Check if database is empty to run seed data
    if User.query.first() is None:
        print("Database is empty. Seeding default data...")

        # 1. Create default system author
        admin = User(
            username="aether_system",
            email="system@aetherblog.dev",
            bio="The official AetherBlog system engine account. Providing default guidelines, technical notes, and updates.",
            is_admin=True,
        )
        admin.set_password("aether_secure_pass_9988")
        db.session.add(admin)
        db.session.commit()  # Commit to generate admin.id

        # 2. Create default categories
        categories_list = [
            "Technology",
            "AI & Machine Learning",
            "Development Notes",
            "General",
        ]
        categories_map = {}
        for cat_name in categories_list:
            cat = Category(name=cat_name, slug=Category.generate_slug(cat_name))
            db.session.add(cat)
            categories_map[cat_name] = cat
        db.session.commit()

        # 3. Create default tags
        tags_list = ["flask", "sqlite", "ai-copilot", "webdev", "python"]
        tags_map = {}
        for tag_name in tags_list:
            t = Tag(name=tag_name)
            db.session.add(t)
            tags_map[tag_name] = t
        db.session.commit()

        # 4. Create a default Banner
        welcome_banner = Banner(
            title="AetherBlog Co-pilot Platform",
            subtitle="Write, generate, and optimize your blog posts with cutting-edge AI assistance powered by Groq LPU™.",
            image_url="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=1200&q=80",
            link_url=None,
            active=True,
        )
        db.session.add(welcome_banner)
        db.session.commit()

        # 5. Create default Welcome Blog Post
        welcome_post = Post(
            title="Welcome to AetherBlog - AI-Co-piloted Blogging platform",
            slug="welcome-to-aetherblog-ai-co-piloted-blogging-platform",
            content=(
                "Welcome to AetherBlog! This is a state-of-the-art blogging application built using a clean MVC "
                "architecture with Python, Flask, SQLite, and Bootstrap 5.\n\n"
                "### Key Features of this Platform:\n"
                "1. **Clean MVC Architecture**: Routes and view controllers are separated from database models "
                "using Flask Blueprints.\n"
                "2. **Secure User Access**: Fully equipped with User Registration, hashed passwords using Werkzeug "
                "security helpers, and persistent sessions handled via Flask-Login.\n"
                "3. **Dynamic Responsive Layout**: Built with a gorgeous customized Bootstrap 5 dark theme featuring "
                "glassmorphic navigation panels, glowing hover visual animations, and responsive grids.\n"
                "4. **Interactive Comments & Live Search**: Supports instant AJAX comment posting without page "
                "reloads and query matching search functionality.\n"
                "5. **Groq AI blogging assistant**: Out-of-the-box support for the Groq completions API to generate outlines, "
                "summarize drafts, and recommend keywords.\n\n"
                "### How to Activate the Groq AI Co-pilot:\n"
                "The system is pre-configured for Groq API integration. To unlock full AI features:\n"
                "1. Open the `.env` file in the root directory of this project.\n"
                "2. Add your Groq API key to the `GROQ_API_KEY` parameter.\n"
                "3. Restart the web server. When creating or editing articles, click the AI Co-pilot helper buttons to generate outlines, "
                "summaries, and tags in real-time.\n\n"
                "Start writing now by registering a new account using the 'Sign Up' button in the navigation header!"
            ),
            summary="Welcome to AetherBlog. Explore our clean MVC architecture, user security, responsive dark design, and live Groq AI blogging assistant features.",
            featured_image="https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&w=800&q=80",
            category_id=categories_map["Technology"].id,
            status="Published",
            author_id=admin.id,
        )

        # Associate tags
        welcome_post.tags.append(tags_map["flask"])
        welcome_post.tags.append(tags_map["webdev"])
        welcome_post.tags.append(tags_map["ai-copilot"])
        welcome_post.tags.append(tags_map["python"])

        db.session.add(welcome_post)
        db.session.commit()
        print("Database seeded successfully.")


if __name__ == "__main__":
    with app.app_context():
        seed_database()

    print("Starting AetherBlog Flask Dev Server on http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
