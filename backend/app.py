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
    print("AVISO: Chave API não encontrada.")
else:
    genai.configure(api_key=API_KEY)

def load_db():
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, 'vibes_db.json')
        with open(db_path, 'r', encoding='utf-8') as f:
            print("Banco de dados carregado.")
            return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar DB: {e}")
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
    text = data.get('text', '').strip()

    if not text:
        return jsonify({"error": "Input vazio"}), 400

    try:
        print(f"Recebido: {text}")

        model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')

        # PROMPT MELHORADO COM SUPORTE A MÚLTIPLAS VIBES
        prompt = f"""
Você é o **VibeCheck**, um especialista musical inteligente e extremamente preciso.

Entrada do usuário: "{text}"

Playlists disponíveis: {list(VIBES_DB.keys())}

--- MODO DE RESPOSTA ---

1) Se o usuário pedir 1 ou mais vibes/gêneros, responda:
VIBE:vibe1,vibe2,vibe3

2) Se o usuário quiser conversar:
CHAT:resposta curta

Nunca envie nada fora disso.
"""

        response = model.generate_content(prompt)
        raw_output = response.text.strip()

        print(f"Resposta da IA: {raw_output}")

        # ---------------------------------
        # SUPORTE A MÚLTIPLAS VIBES AQUI 🔥
        # ---------------------------------
        if raw_output.startswith("VIBE:"):
            vibe_raw = raw_output.replace("VIBE:", "").strip().lower()

            # quebrar em lista
            vibe_list = [v.strip() for v in vibe_raw.split(",") if v.strip()]

            results = []

            for vibe in vibe_list:
                if vibe in VIBES_DB:
                    results.append({
                        "found": True,
                        "vibe": vibe,
                        "message": VIBES_DB[vibe]["message"],
                        "title": VIBES_DB[vibe]["title"],
                        "spotify_id": extract_spotify_id(VIBES_DB[vibe]["url"])
                    })
                else:
                    results.append({
                        "found": False,
                        "vibe": vibe,
                        "message": f"Captei a vibe '{vibe}', mas ainda não tenho playlist cadastrada."
                    })

            return jsonify({
                "multiple": True,
                "results": results
            })

        elif raw_output.startswith("CHAT:"):
            return jsonify({
                "multiple": False,
                "found": False,
                "message": raw_output.replace("CHAT:", "").strip()
            })

        # fallback
        return jsonify({
            "found": False,
            "message": "Não entendi. Quer uma playlist ou quer conversar?"
        })

    except Exception as e:
        print(f"❌ Erro Interno: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("VIBECHECK ATIVADO ⚡")
    app.run(debug=True, port=5000)
