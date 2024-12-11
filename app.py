from flask import Flask, render_template, jsonify
import requests

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('mouradaustade.html')

@app.route('/api/matches')
def get_matches():
    # Récupération des matches depuis l'API externe
    try:
        response = requests.get('URL_DE_VOTRE_API_EXTERNE')
        matches = response.json()
        return jsonify(matches)
    except Exception as e:
        print(f"Erreur: {e}")
        return jsonify([])

@app.route('/stream/<match_id>')
def stream(match_id):
    # Logique pour le streaming
    return render_template('stream.html', match_id=match_id)

if __name__ == '__main__':
    app.run(debug=True)
