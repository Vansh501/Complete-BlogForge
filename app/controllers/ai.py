import os
import requests
from flask import Blueprint, request, jsonify
from flask_login import login_required

ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/ai/assist', methods=['POST'])
@login_required
def assist():
    data = request.get_json() or {}
    action = data.get('action')
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    topic = data.get('topic', '').strip()
    keywords = data.get('keywords', '').strip()
    text_to_process = data.get('text_to_process', '').strip()
    lang = data.get('lang', 'english').strip().lower()
    tone = data.get('tone', 'standard').strip().lower()

    # Retrieve credentials
    api_key = os.getenv('GROQ_API_KEY')
    model = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')

    # If API Key is missing, return a helpful instructions response
    if not api_key:
        return jsonify({
            'status': 'offline',
            'message': 'Groq API Key is not configured. Add GROQ_API_KEY to your .env file to enable live AI features.',
            'mock_data': get_mock_ai_response(action, data, lang, tone)
        }), 200

    # Build prompt based on action
    if action == 'title':
        if not topic:
            return jsonify({'error': 'Topic or keywords are required to generate titles.'}), 400
        prompt = f"Generate 5 catchy, engaging, SEO-optimized blog post titles for the topic/keywords: '{topic}'. Return ONLY a clean numbered list, with no intro or outro comments."
    elif action == 'seo_content':
        if not title:
            return jsonify({'error': 'Post title is required to generate SEO content.'}), 400
        prompt = f"Write a comprehensive, SEO-optimized blog post body for the title: '{title}' and using keywords: '{keywords}'. Format the content in clean HTML tags (such as h3, h4, p, ul, li, strong, em). Do not output markdown. Do not include h1 or body/html wrappers."
    elif action == 'intro':
        if not title:
            return jsonify({'error': 'Post title is required to generate an introduction.'}), 400
        prompt = f"Write a compelling, hook-filled introduction paragraph (under 150 words) for a blog post titled: '{title}'. Return the result as clean HTML paragraph tags."
    elif action == 'conclusion':
        if not title:
            return jsonify({'error': 'Post title is required to generate a conclusion.'}), 400
        prompt = f"Write a strong, memorable conclusion paragraph (under 150 words) with a call-to-action for a blog post titled: '{title}', based on the following content summary:\n\n{content}. Return the result as clean HTML paragraph tags."
    elif action == 'rewrite':
        target_text = text_to_process or content
        if not target_text:
            return jsonify({'error': 'Content is required to rewrite.'}), 400
        prompt = f"Rewrite the following blog content to make it more professional, engaging, and flow better. Preserve original meaning. Return the result in clean HTML tags:\n\n{target_text}"
    elif action == 'expand':
        target_text = text_to_process or content
        if not target_text:
            return jsonify({'error': 'Content is required to expand.'}), 400
        prompt = f"Expand the following paragraph or sentence by adding descriptive details, context, and clear explanations. Maintain a natural, engaging tone. Return the result in clean HTML tags:\n\n{target_text}"
    elif action == 'faq':
        if not content:
            return jsonify({'error': 'Content is required to generate an FAQ section.'}), 400
        prompt = f"Based on this blog content, generate a Frequently Asked Questions (FAQ) section containing 3 to 5 questions and answers. Format it as styled HTML (use h3 for header, strong/p for questions and answers):\n\n{content}"
    elif action == 'meta_description':
        target_text = content or title
        if not target_text:
            return jsonify({'error': 'Content or title is required to generate a meta description.'}), 400
        prompt = f"Write a highly engaging, SEO-friendly meta description (under 160 characters) summarizing the following content. Focus on attracting search engine clicks. Do not include quotes or intro text:\n\n{target_text}"
    elif action == 'outline':
        if not title:
            return jsonify({'error': 'Title is required to generate an outline.'}), 400
        prompt = f"Create a detailed, engaging blog post outline for the topic: '{title}'. Use markdown bullet points and headings. Add brief structural notes under each heading."
    elif action == 'summary':
        if not content:
            return jsonify({'error': 'Content is required to generate a summary.'}), 400
        prompt = f"Write a concise, engaging 2-sentence summary (max 300 characters) for a blog post based on this content. Focus on the main hook or key takeaway:\n\n{content}"
    elif action == 'tags':
        if not content:
            return jsonify({'error': 'Content is required to generate tag suggestions.'}), 400
        prompt = f"Analyze the following blog content and suggest 3 to 5 relevant SEO keywords or tags. Return ONLY a single line containing comma-separated lowercase tags, without numbering, bullets, introduction, or quotes. Example: python, flask, webdev\n\nContent:\n{content}"
    elif action == 'translate':
        if not text_to_process:
            return jsonify({'error': 'Text is required to translate.'}), 400
        prompt = f"Translate the following text into the {lang} language (using native {lang} script). Preserve all HTML tags, structure, and the exact ' ||| ' separator delimiter. Do not write any intro or comments:\n\n{text_to_process}"
    else:
        return jsonify({'error': 'Invalid action requested.'}), 400

    # Append tone and language styling overrides
    if tone == 'friendly':
        prompt += " Use a friendly, warm, casual, conversational, and highly approachable language style."
    if lang != 'english':
        prompt += f" IMPORTANT: Write the entire output (including titles, text, headers, and bullet points) in the {lang} language. Translate any generated concepts/titles/outlines to {lang} using its native script."

    # Call Groq API
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
                    "content": "You are a professional blogging and SEO co-pilot. Keep responses clean, targeted, and formatted correctly."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.5,
            "max_tokens": 1000
        }

        response = requests.post(url, headers=headers, json=payload, timeout=12)
        
        if response.status_code == 200:
            res_data = response.json()
            ai_text = res_data['choices'][0]['message']['content'].strip()
            return jsonify({
                'status': 'success',
                'result': ai_text
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f"Groq API error (Status {response.status_code}): {response.text}"
            }), 502

    except requests.exceptions.RequestException as e:
        err_msg = str(e)
        is_conn_error = "NameResolutionError" in err_msg or "Failed to resolve" in err_msg or "Max retries exceeded" in err_msg or "Connection" in err_msg
        
        if is_conn_error:
            return jsonify({
                'status': 'offline',
                'message': 'Unable to connect to the internet or resolve api.groq.com. Operating in Offline/Fallback Mode.',
                'mock_data': get_mock_ai_response(action, data, lang, tone)
            }), 200
            
        return jsonify({
            'status': 'error',
            'message': f"Failed to connect to Groq API: {err_msg}"
        }), 503

def get_mock_ai_response(action, data, lang='english', tone='standard'):
    """Provides a preview response in case Groq API key is not configured."""
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    topic = data.get('topic', '').strip()
    keywords = data.get('keywords', '').strip()
    text_to_process = data.get('text_to_process', '').strip()

    # Translation dictionary for mock responses
    t_map = {
        'hindi': {
            'title_prefix': 'शीर्षक',
            'guide': 'मार्गदर्शिका',
            'tools': 'महत्वपूर्ण उपकरण',
            'future': 'भविष्य',
            'introduction': 'प्रस्तावना',
            'key_concepts': 'मुख्य अवधारणाएं',
            'steps': 'व्यावहारिक कदम',
            'conclusion': 'निष्कर्ष',
            'faq_title': 'अक्सर पूछे जाने वाले प्रश्न',
            'q1': 'Q1: इस विषय के लिए सर्वोत्तम अभ्यास क्या हैं?',
            'a1': 'A1: निरंतरता ही कुंजी है। हमेशा स्पष्ट रूपरेखा से शुरुआत करें।',
            'q2': 'Q2: यह खोज इंजन अनुकूलन (SEO) में कैसे मदद करता है?',
            'a2': 'A2: कीवर्ड को स्वाभाविक रूप से हेडर में रखने से दृश्यता बढ़ती है।',
            'intro_text': 'क्या आपने कभी सोचा है कि {title} की चुनौतियों को आसानी से कैसे हल किया जाए? इस लेख में, हम गहराई से चर्चा करेंगे और व्यावहारिक मार्गदर्शिका प्रदान करेंगे।',
            'conclusion_text': 'संक्षेप में कहें तो, {title} की सफलता निरंतर अभ्यास पर निर्भर करती है। आशा है कि यह जानकारी आपके काम आएगी। अपने विचार कमेंट में साझा करें!',
            'tags': 'वेब-विकास, ट्यूटोरियल, प्रोग्रामिंग, ब्लॉगिंग',
            'meta': 'हमारे गाइड का अन्वेषण करें। संरचनात्मक डिजाइन पैटर्न सीखें, कोड स्निपेट देखें और अपने एप्लिकेशन प्रवाह को आज ही अनुकूलित करें!'
        },
        'punjabi': {
            'title_prefix': 'ਸਿਰਲੇਖ',
            'guide': 'ਮਾਰਗਦਰਸ਼ਕ',
            'tools': 'ਮਹੱਤਵਪੂਰਨ ਸਾਧਨ',
            'future': 'ਭਵਿੱਖ',
            'introduction': 'ਜਾਣ-ਪਛਾਣ',
            'key_concepts': 'ਮੁੱਖ ਸੰਕਲਪ',
            'steps': 'ਵਿਵਹਾਰਕ ਕਦਮ',
            'conclusion': 'ਸਿੱਟਾ',
            'faq_title': 'ਅਕਸਰ ਪੁੱਛੇ ਜਾਣ ਵਾਲੇ ਸਵਾਲ',
            'q1': 'Q1: ਇਸ ਵਿਸ਼ੇ ਲਈ ਸਭ ਤੋਂ ਵਧੀਆ ਅਭਿਆਸ ਕੀ ਹਨ?',
            'a1': 'A1: ਨਿਰੰਤਰਤਾ ਹੀ ਕੁੰਜੀ ਹੈ। ਹਮੇਸ਼ਾ ਸਪਸ਼ਟ ਰੂਪ ਰੇਖਾ ਨਾਲ ਸ਼ੁਰੂ ਕਰੋ।',
            'q2': 'Q2: ਇਹ ਸਰਚ ਇੰਜਨ ਔਪਟੀਮਾਈਜੇਸ਼ਨ (SEO) ਵਿੱਚ ਕਿਵੇਂ ਮਦਦ ਕਰਦਾ ਹੈ?',
            'a2': 'A2: ਕੀਵਰਡਸ ਨੂੰ ਸਿਰਲੇਖਾਂ ਵਿੱਚ ਰੱਖਣ ਨਾਲ ਵਿਜ਼ੀਬਿਲਟੀ ਵਧਦੀ ਹੈ।',
            'intro_text': 'ਕੀ ਤੁਸੀਂ ਕਦੇ ਸੋਚਿਆ ਹੈ ਕਿ {title} ਦੀਆਂ ਚੁਣੌਤੀਆਂ ਨੂੰ ਕਿਵੇਂ ਹੱਲ ਕਰਨਾ ਹੈ? ਇਸ ਲੇਖ ਵਿੱਚ ਅਸੀਂ ਇਸ ਬਾਰੇ ਵਿਸਥਾਰ ਵਿੱਚ ਗੱਲ ਕਰਾਂਗੇ।',
            'conclusion_text': 'ਸੰਖੇਪ ਵਿੱਚ, {title} ਵਿੱਚ ਸਫਲਤਾ ਲਗਾਤਾਰ ਮਿਹਨਤ ਉੱਤੇ ਨਿਰਭਰ ਕਰਦੀ ਹੈ। ਉਮੀਦ ਹੈ ਇਹ ਜਾਣਕਾਰੀ ਲਾਹੇਵੰਦ ਹੋਵੇਗੀ। ਕਮੈਂਟ ਵਿੱਚ ਆਪਣੇ ਵਿਚਾਰ ਸਾਂਝੇ ਕਰੋ!',
            'tags': 'ਵੈਬ-ਵਿਕਾਸ, ਟਿਊਟੋਰਿਅਲ, ਪ੍ਰੋਗਰਾਮਿੰਗ, ਬਲੌਗਿੰਗ',
            'meta': 'ਸਾਡੀ ਗਾਈਡ ਦੀ ਪੜਚੋਲ ਕਰੋ। ਢਾਂਚਾਗਤ ਡਿਜ਼ਾਈਨ ਪੈਟਰਨ ਸਿੱਖੋ, ਕੋਡ ਸਨਿੱਪਟ ਦੇਖੋ ਅਤੇ ਅੱਜ ਹੀ ਆਪਣੇ ਐਪਲੀਕੇਸ਼ਨ ਪ੍ਰਵਾਹ ਨੂੰ ਅਨੁਕੂਲ ਬਣਾਓ!'
        },
        'gujarati': {
            'title_prefix': 'શીર્ષક',
            'guide': 'માર્ગદર્શિકા',
            'tools': 'મહત્વપૂર્ણ સાધનો',
            'future': 'ભવિષ્ય',
            'introduction': 'પ્રસ્તાવના',
            'key_concepts': 'મુખ્ય ખ્યાલો',
            'steps': 'વ્યવહારુ પગલાં',
            'conclusion': 'નિષ્કર્ષ',
            'faq_title': 'વારંવાર પૂછાતા પ્રશ્નો',
            'q1': 'Q1: આ વિષય માટે શ્રેષ્ઠ પદ્ધતિઓ શું છે?',
            'a1': 'A1: સુસંગતતા જ ચાવી છે. helmets સ્પષ્ટ રૂપરેખાથી પ્રારંભ કરો.',
            'q2': 'Q2: આ સર્ચ એન્જિન ઓપ્ટિમાઇઝેશન (SEO) માં કેવી રીતે મદદ કરે છે?',
            'a2': 'A2: કીવર્ડ્સને હેડરમાં કુદરતી રીતે મૂકવાથી દૃશ્યતા વધે છે.',
            'intro_text': 'શું તમે ક્યારેય વિચાર્યું છે કે {title} ના પડકારોને કેવી રીતે સરળતાથી ઉકેલી શકાય? આ લેખમાં આપણે વિગતવાર ચર્ચા કરીશું.',
            'conclusion_text': 'ટૂંકમાં, {title} માં સફળતા સતત પ્રયત્નો પર આધાર રાખે છે. આશા છે કે આ માહિતી ઉપયોગી સાબિત થશે. તમારા વિચારો કમેન્ટમાં જણાવો!',
            'tags': 'વેબ-વિકાસ, ટ્યુટોરીયલ, પ્રોગ્રામિંગ, બ્લોગિંગ',
            'meta': 'અમારી માર્ગદર્શિકાનું અન્વેષણ કરો. માળખાકીય ડિઝાઇન પેટર્ન શીખો, કોડ સ્નિપેટ્સ જુઓ અને આજે જ તમારા એપ્લિકેશન પ્રવાહને ઓપ્ટિમાઇઝ કરો!'
        }
    }

    # Friendly tone prefix adjustment
    tone_prefix = ""
    if tone == 'friendly':
        if lang == 'english':
            tone_prefix = "Hey there! Let's keep it friendly: "
        elif lang == 'hindi':
            tone_prefix = "नमस्ते दोस्त! चलिए इसे थोड़ा आसान बनाते हैं: "
        elif lang == 'punjabi':
            tone_prefix = "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ ਦੋਸਤੋ! ਆਓ ਇਸਨੂੰ ਥੋੜਾ ਸੌਖਾ ਬਣਾਈਏ: "
        elif lang == 'gujarati':
            tone_prefix = "નમસ્તે મિત્ર! ચાલો આને થોડું સરળ બનાવીએ: "

    if action == 'title':
        tp = topic or 'Software Engineering'
        if lang in t_map:
            t_obj = t_map[lang]
            return (
                f"1. {tp} {t_obj['guide']}: 2026 {t_obj['future']}\n"
                f"2. {tp} {t_obj['tools']}\n"
                f"3. {tp} {t_obj['faq_title']}"
            )
        return (
            f"1. Mastering {tp} in 2026: A Comprehensive Guide\n"
            f"2. 5 Essential Tools for {tp} You Need to Know\n"
            f"3. Demystifying {tp}: Common Pitfalls and Solutions\n"
            f"4. The Future of {tp}: Key Trends and Insights\n"
            f"5. How to Build Your First {tp} Application From Scratch"
        )
    elif action == 'seo_content':
        t = title or 'A Guide to Modern Web Development'
        kw = keywords or 'webdev, programming'
        if lang in t_map:
            t_obj = t_map[lang]
            return (
                f"<h3>{t_obj['introduction']}</h3>\n"
                f"<p>{tone_prefix}<strong>{t}</strong> {t_obj['intro_text'].format(title=t)}</p>\n\n"
                f"<h3>{t_obj['key_concepts']}</h3>\n"
                f"<p>{t_obj['steps']}</p>\n\n"
                f"<h3>{t_obj['conclusion']}</h3>\n"
                f"<p>{t_obj['conclusion_text'].format(title=t)}</p>"
            )
        return (
            f"<h3>Introduction</h3>\n"
            f"<p>{tone_prefix}In today's fast-paced digital world, mastering <strong>{t}</strong> is more important than ever. Whether you are a beginner starting your coding journey or a seasoned veteran looking to upgrade your tech stack, aligning your work with keywords like <em>{kw}</em> will maximize reach.</p>\n\n"
            f"<h3>Key Technical Foundations</h3>\n"
            f"<p>Building robust structures requires a keen understanding of architectural patterns. Focus on clean code principles, modular components, and automated testing pipelines to ensure software scalability and reliability.</p>\n\n"
            f"<ul>\n"
            f"  <li><strong>Modular Design</strong>: Keep functions single-purpose and clean.</li>\n"
            f"  <li><strong>SEO Optimization</strong>: Inject keyword metrics naturally across headers.</li>\n"
            f"  <li><strong>Fast Response</strong>: Cache static resources and minify bundles.</li>\n"
            f"</ul>\n\n"
            f"<h3>Conclusion</h3>\n"
            f"<p>By applying these methodologies, you create systems that perform flawlessly. Stay curious, code daily, and continue exploring new horizons!</p>"
        )
    elif action == 'intro':
        t = title or 'My Post'
        if lang in t_map:
            return f"<p>{tone_prefix}{t_map[lang]['intro_text'].format(title=t)}</p>"
        return f"<p>{tone_prefix}Have you ever wondered how to effectively tackle the challenges of <strong>{t}</strong>? In this article, we dive deep into the core concepts, outline key strategies, and provide practical walk-throughs to get you up and running in minutes.</p>"
    elif action == 'conclusion':
        t = title or 'My Post'
        if lang in t_map:
            return f"<p>{tone_prefix}{t_map[lang]['conclusion_text'].format(title=t)}</p>"
        return f"<p>{tone_prefix}To summarize, success with <strong>{t}</strong> lies in consistent execution and testing. We hope this guide empowers you to optimize your development flow. What are your thoughts on this approach? Let us know in the comments below!</p>"
    elif action == 'rewrite':
        text = text_to_process or content or 'Write content here.'
        return f"<p>{tone_prefix}<strong>Polished Draft ({lang}):</strong></p><p>{text}</p>"
    elif action == 'expand':
        text = text_to_process or content or 'Write content here.'
        return f"<p>{tone_prefix}{text} (Expanded in {lang})</p>"
    elif action == 'faq':
        if lang in t_map:
            t_obj = t_map[lang]
            return (
                f"<h3>{t_obj['faq_title']}</h3>\n"
                f"<p><strong>{t_obj['q1']}</strong><br>{t_obj['a1']}</p>\n"
                f"<p><strong>{t_obj['q2']}</strong><br>{t_obj['a2']}</p>"
            )
        return (
            f"<h3>Frequently Asked Questions</h3>\n"
            f"<p><strong>Q1: What are the best practices for this topic?</strong><br>"
            f"A1: The key is consistency. Always start with clear structural outlines, draft concise descriptions, and write automated unit tests to verify requirements.</p>\n"
            f"<p><strong>Q2: How does this help search engine optimization (SEO)?</strong><br>"
            f"A2: Naturally placing targeted keywords within H2/H3 headers and paragraphs boosts visibility in organic search queries.</p>"
        )
    elif action == 'meta_description':
        t = title or 'My Post'
        if lang in t_map:
            return t_map[lang]['meta']
        return f"Explore our guide on {t}. Learn structural design patterns, check out code snippets, and optimize your application flow today!"
    elif action == 'outline':
        t = title or 'My Amazing Post'
        return (
            f"### Mock Outline ({lang}): {t}\n"
            f"1. **Introduction**\n"
            f"2. **Core Concepts**\n"
            f"3. **Conclusion**"
        )
    elif action == 'summary':
        if not content:
            return "This is a placeholder summary."
        return f"Summary ({lang}): {content[:100]}..."
    elif action == 'tags':
        if lang in t_map:
            return t_map[lang]['tags']
        return "webdevelopment, tutorial, software-design, programming"
    elif action == 'translate':
        text = text_to_process or ''
        if '|||' in text:
            parts = text.split('|||')
            t_part = parts[0].strip()
            c_part = parts[1].strip()
            if lang == 'hindi':
                return f"सच्ची दोस्ती की शक्ति: सच्ची दोस्ती को कैसे पोषित करें ||| <p>सच्ची दोस्ती के बारे में अनुवादित सामग्री।</p> {c_part}"
            elif lang == 'punjabi':
                return f"ਸੱਚੀ ਦੋਸਤੀ ਦੀ ਸ਼ਕਤੀ: ਸੱਚੀ ਦੋਸਤੀ ਨੂੰ ਕਿਵੇਂ ਪਾਲਣਾ ਹੈ ||| <p>ਸੱਚੀ ਦੋਸਤੀ ਬਾਰੇ ਅਨੁਵਾਦਿਤ ਸਮੱਗਰੀ।</p> {c_part}"
            elif lang == 'gujarati':
                return f"સાચી મિત્રતાની શક્તિ: સાચી મિત્રતાને કેવી રીતે પોષવી ||| <p>સાચી મિત્રતા વિશે અનુવાદિત સામગ્રી।</p> {c_part}"
            return f"{t_part} (Translated) ||| {c_part} (Translated)"
        return f"Translated text ({lang}): {text}"
    return ""
