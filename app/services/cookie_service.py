from flask import request, jsonify
import os

def save_cookies(request):
    try:
        cookies_text = request.form.get('cookies', '')
        if cookies_text:
            with open('cookies.txt', 'w', encoding='utf-8') as f:
                f.write(cookies_text)
            return jsonify({'success': True, 'message': 'Cookies saved successfully'})
        return jsonify({'success': False, 'error': 'No cookies provided'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
