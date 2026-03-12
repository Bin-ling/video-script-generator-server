from database import db
import json

def insert_analysis(data):
    return db.insert_analysis(data)

def get_all_analyses():
    return db.get_all_analyses()

def get_analysis_by_id(analysis_id):
    return db.get_analysis_by_id(analysis_id)

def delete_analysis(analysis_id):
    return db.delete_analysis(analysis_id)

def get_all_prompts():
    return db.get_all_prompts()

def update_prompt(request):
    data = request.json
    prompt_id = data.get('id')
    content = data.get('content')
    if prompt_id and content:
        success = db.update_prompt(prompt_id, content)
        return {'success': success}
    return {'success': False}

def get_prompt_by_name(name):
    return db.get_prompt_by_name(name)
