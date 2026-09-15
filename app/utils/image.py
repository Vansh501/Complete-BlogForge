import os
import uuid
from PIL import Image
from flask import current_app
from werkzeug.utils import secure_filename

def save_and_resize_image(file, subfolder='posts', max_width=1200):
    """
    Saves an uploaded image, resizes it if its width exceeds max_width,
    and returns the relative URL to the saved file.
    """
    if not file or file.filename == '':
        return None

    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
        return None

    # Determine saving path
    upload_dir = os.path.join(current_app.static_folder, 'uploads', subfolder)
    os.makedirs(upload_dir, exist_ok=True)
    
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    dest_path = os.path.join(upload_dir, unique_filename)

    try:
        # Open image with Pillow using context manager to release file locks on Windows
        with Image.open(file) as img:
            # Check and convert color mode if saving as JPEG (e.g. RGBA -> RGB)
            if img.mode in ('RGBA', 'LA') and ext in ['.jpg', '.jpeg']:
                img = img.convert('RGB')

            # Resize if width is larger than max_width
            width, height = img.size
            if width > max_width:
                new_height = int((max_width / width) * height)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            # Save image
            img.save(dest_path)
        return f"/static/uploads/{subfolder}/{unique_filename}"
    except Exception as e:
        print(f"Error processing/saving image: {e}")
        return None

def delete_old_image(image_url):
    """
    Deletes an image from disk given its relative web URL.
    """
    if not image_url or not image_url.startswith('/static/uploads/'):
        return

    # Convert web URL to local file path
    rel_path = image_url.lstrip('/')
    file_path = os.path.join(current_app.root_path, rel_path)
    
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Error deleting old image {file_path}: {e}")
