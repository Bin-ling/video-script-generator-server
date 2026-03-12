from flask import Flask
from app.routes.main_routes import register_routes
from app.routes.module_routes import module_bp
from app.services.analysis_service import init_llm
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder="static")
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
os.makedirs("static/frames", exist_ok=True)

API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME")

init_llm(API_KEY, BASE_URL, MODEL_NAME)

register_routes(app)
app.register_blueprint(module_bp)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
