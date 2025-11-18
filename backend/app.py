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
    print("AVISO: Chave GEMINI_API_KEY não encontrada.")
else:
    genai.configure(api_key=API_KEY)

def load_db():
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, 'vibes_db.json')
        with open(db_path, 'r', encoding='utf-8') as f:
            print(f"Banco de dados carregado.")
            return json.load(f)
    except Exception as e:
        print(f"❌ Erro ao carregar DB: {e}")
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
    text = data.get('text', '')

    if not text:
        return jsonify({"error": "Input vazio"}), 400

    try:
        print(f"Recebido: {text}")
        
        model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')
        
        prompt = f"""
        Você é o VibeCheck, um especialista musical inteligente e descolado.
        
        Entrada do usuário: "{text}"
        
        Playlists disponíveis no sistema: {list(VIBES_DB.keys())}.
        
        SUA MISSÃO (Siga a lógica abaixo):
        
        1. RECOMENDAÇÃO: Se o usuário pedir música, playlist, ou descrever um sentimento/cenário (ex: "estou triste", "focar", "quero festa"):
           - Responda APENAS no formato: VIBE:chave_da_categoria
           - Exemplo: VIBE:foco
           
        2. CONVERSA: Se o usuário fizer uma pergunta sobre música, opinar, ou cumprimentar (ex: "Quem é o rei do pop?", "Gosta de Rock?", "Olá"):
           - Responda de forma curta, amigável e interessante em Português (máximo 2 frases).
           - Responda no formato: CHAT:Sua resposta aqui
           
        3. OUTROS: Se não for sobre música:
           - Responda: CHAT:Eu só entendo de música! Que tal me pedir uma playlist? 🎧
        """
        
        response = model.generate_content(prompt)
        raw_output = response.text.strip()
        print(f"Resposta da IA: {raw_output}")

        if raw_output.startswith("VIBE:"):
            vibe_key = raw_output.replace("VIBE:", "").strip().lower()
            vibe_key = re.sub(r'[^a-z]', '', vibe_key) # Limpa sujeira

            result = VIBES_DB.get(vibe_key)
            
            if result:
                return jsonify({
                    "found": True,
                    "vibe": vibe_key,
                    "message": result['message'],
                    "title": result['title'],
                    "spotify_id": extract_spotify_id(result['url'])
                })
            else:
                return jsonify({
                    "found": False, 
                    "message": "Captei a vibe, mas não tenho uma playlist exata para isso ainda. Tente algo como 'foco' ou 'festa'!"
                })

        elif raw_output.startswith("CHAT:"):
            chat_response = raw_output.replace("CHAT:", "").strip()
            return jsonify({
                "found": False, 
                "message": chat_response
            })
            
        else:
            return jsonify({"found": False, "message": "Não entendi. Quer conversar sobre música ou uma playlist?"})

    except Exception as e:
        print(f"❌ Erro Interno: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("VIBECHECK ATIVADO ")
    app.run(debug=True, port=5000)