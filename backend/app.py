import os
import json
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("AVISO: Chave GEMINI_API_KEY não encontrada")
else:
    genai.configure(api_key=API_KEY)

def load_db():
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, 'vibes_db.json')
        with open(db_path, 'r', encoding='utf-8') as f:
            print(f"✅ DB Carregado.")
            return json.load(f)
    except Exception as e:
        print(f"Erro Crítico ao carregar DB: {e}")
        return {}

VIBES_DB = load_db()

def extract_spotify_id(url):
    match = re.search(r'(?:playlist|track|album)[/:]([a-zA-Z0-9]+)', url)
    return match.group(1) if match else None

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "online"})

@app.route('/api/recommend', methods=['POST'])
def recommend():
    data = request.json
    user_text = data.get('text', '')

    if not user_text:
        return jsonify({"error": "Texto vazio"}), 400

    try:
        print(f"Recebido: {user_text}")
        model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')
        prompt = f"""
        Atue como classificador de sentimentos musicais.
        Categorias: {list(VIBES_DB.keys())}.
        Texto do usuário: "{user_text}"
        Responda APENAS a chave da categoria (ex: "foco").
        Se não entender, responda "padrao".
        """
        
        response = model.generate_content(prompt)
        vibe_key = re.sub(r'[^a-z]', '', response.text.strip().lower())
        print(f"Classificado como: {vibe_key}")

        result = VIBES_DB.get(vibe_key)
        if not result:
            return jsonify({"found": False, "message": "Não entendi a vibe."})

        return jsonify({
            "found": True,
            "vibe": vibe_key,
            "message": result['message'],
            "title": result['title'],
            "spotify_id": extract_spotify_id(result['url'])
        })

    except Exception as e:
        print(f"Erro: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("SERVIDOR ONLINE")
    app.run(debug=True, port=5000)