# backend/app.py
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
from dotenv import load_dotenv
from routes.game_routes import game_bp
from services.steam_services import SteamService

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')

CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# register blueprints
app.register_blueprint(game_bp, url_prefix='/api')

@app.route('/')
def home():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "service": "BacklogBuddy"}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)