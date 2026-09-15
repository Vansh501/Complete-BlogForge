# Walkthrough: Database Models Restructuring

The database layer of the Blog Management System has been fully updated using Flask-SQLAlchemy to align with the new schema specifications.

---

## 🗄️ Database Tables Schema

The database model in [app/models.py](file:///C:/Users/ASUS/.gemini/antigravity/scratch/blog-system/app/models.py) now manages six tables with clean relational integrity:

1. **`users` Table (`User` Model)**:
   * Has many `posts` (backref `author`).
   * Has many `comments` (backref `author`).

2. **`categories` Table (`Category` Model)**:
   * Has many `posts` (backref `category`).
   * Attributes: `id`, `name`, `slug` (URL-friendly).

3. **`tags` Table (`Tag` Model)**:
   * Many-to-Many relationship with `posts` via junction table `post_tags`.

4. **`posts` Table (`Post` Model)**:
   * Belongs to one `author` (`author_id` -> `users.id`, replacement for `user_id`).
   * Belongs to one `category` (`category_id` -> `categories.id`).
   * Attributes: `title`, `slug`, `content`, `summary`, `featured_image` (new featured image URL support), `status` ('Published' / 'Draft' capitalized), `created_at`, `updated_at`.

5. **`banners` Table (`Banner` Model)**:
   * Stores promotional or announcement graphics for the home feed carousel.
   * Attributes: `id`, `title`, `subtitle`, `image_url`, `link_url`, `active` (boolean), `created_at`.

6. **`contact_messages` Table (`ContactMessage` Model)**:
   * Handles user inquiries.
   * Attributes: `id`, `name`, `email`, `subject`, `message`, `created_at`.

---

## 🎨 Layout and Controller Integration

* **Home Feed Carousel** ([app/views/blog/index.html](file:///C:/Users/ASUS/.gemini/antigravity/scratch/blog-system/app/views/blog/index.html)): Integrates a Bootstrap carousel at the top of the feed to rotate active promotional Banners.
* **Categories Sidebar List**: Lists all categories in the right-hand panel alongside post counts and filters the blog feed by category on selection.
* **Post Covers**: Renders the custom `featured_image` if defined for an article, falling back to the unique math-generated HSL background cover if empty.
* **Category Dropdown & Image Link**: Integrated into the write/edit post forms ([app/views/blog/editor.html](file:///C:/Users/ASUS/.gemini/antigravity/scratch/blog-system/app/views/blog/editor.html)).

* **Admin Control Panel**: Restricted to accounts flagged as `is_admin=True` (like the seeded `aether_system` user).
* **Sidebar Management Console**: Provides dedicated controls for platform overview metrics, categories CRUD, post moderations, active homepage carousel banners, and user inquiries inbox.

---

## 🔄 How to Apply and Run

The database tables have been dropped, recreated, and successfully seeded with a default category, tags, welcome post, and homepage banner.

1. **Restart your server** to reload the updated model configurations:
   ```powershell
   cd C:\Users\ASUS\.gemini\antigravity\scratch\blog-system
   .\venv\Scripts\python run.py
   ```
2. Open [http://127.0.0.1:5000](http://127.0.0.1:5000) and explore the carousel, categories listing, and updated writer page!
