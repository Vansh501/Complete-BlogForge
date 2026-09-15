import os
import requests
import json
from app.models import Category

def get_ai_post_suggestions(user_id=None):
    """Generates 3 full suggested mock post objects for new users using Groq or fallbacks."""
    api_key = os.getenv('GROQ_API_KEY')
    model = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')
    
    # Query database categories to align suggestions
    categories = Category.query.all()
    category_list = ", ".join([c.name for c in categories]) if categories else "General, Tech, Lifestyle"
    
    prompt = (
        "Generate exactly 3 creative, engaging, and detailed blog post suggestions/drafts that a new user could publish. "
        f"Each suggestion must correspond to one of these categories: [{category_list}]. "
        "Return the response ONLY as a valid JSON array of objects. Do not include markdown code block syntax (like ```json ... ```), intro, or comments. "
        "Each object in the array MUST contain exactly these fields:\n"
        "- 'title': A catchy, engaging blog post title.\n"
        "- 'category': One of the categories from the list above.\n"
        "- 'summary': A concise 1-sentence hook.\n"
        "- 'content': A complete, rich body paragraph formatted in basic HTML tags (such as p, strong, em).\n"
    )
    
    if api_key:
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a professional blogging and writing co-pilot. You only return valid raw JSON responses."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 1200
            }
            response = requests.post(url, headers=headers, json=payload, timeout=8)
            if response.status_code == 200:
                res_data = response.json()
                text = res_data['choices'][0]['message']['content'].strip()
                # Clean up markdown formats
                if text.startswith('```'):
                    text = text.split('```')[1]
                    if text.startswith('json'):
                        text = text[4:]
                return json.loads(text.strip())
        except Exception:
            pass
            
    # Mock fallback suggestions
    return [
        {
            "title": "Unlocking Creative Writing: How to Overcome Writer's Block",
            "category": "General",
            "summary": "Struggling to find the right words? Discover 5 research-backed strategies to kickstart your writing flow today.",
            "content": "<p>Writer's block can feel like an insurmountable wall. But by changing your physical space, setting micro-goals of 100 words, and practicing free-writing, you can overcome it easily. Remember, draft now, polish later.</p>"
        },
        {
            "title": "The Future of Artificial Intelligence in Everyday Blogging",
            "category": "Tech",
            "summary": "AI tools are shifting from simple auto-completers to powerful creative partners for writers worldwide.",
            "content": "<p>Integrating AI assistance into your blogging routine changes everything. Use it to brainstorm headlines, draft structure outlines, or suggest tags. This leaves you with more time to focus on the human voice and unique insights.</p>"
        },
        {
            "title": "Minimalism in the Workspace: Designing for Deep Focus",
            "category": "General",
            "summary": "Clear desk, clear mind. Learn how clean workspace layouts reduce cognitive load and boost daily throughput.",
            "content": "<p>A cluttered desk leads to a distracted brain. By keeping only essential tools in sight, choosing neutral tones, and adding natural light, you create a sanctuary that invites deep, high-value work.</p>"
        }
    ]

def get_ai_suggested_topics():
    """Generates exactly 3 short writing topics (prompts) using Groq or fallbacks."""
    api_key = os.getenv('GROQ_API_KEY')
    model = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')
    
    if api_key:
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": "Provide exactly 3 short, catchy blog post topics/ideas (max 6 words each). Return them ONLY as a comma-separated list. Do not include numbering, bullets, introduction, or quotes."
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 100
            }
            response = requests.post(url, headers=headers, json=payload, timeout=6)
            if response.status_code == 200:
                res_data = response.json()
                text = res_data['choices'][0]['message']['content'].strip()
                topics = [t.strip().strip('"').strip("'") for t in text.split(',') if t.strip()]
                if len(topics) >= 3:
                    return topics[:3]
        except Exception:
            pass
            
    return [
        "AI trends in web design",
        "Mastering developer productivity",
        "The impact of design systems"
    ]
