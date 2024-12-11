from flask import Flask, render_template, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

# Configuration
SCOREBAT_TOKEN = "MTg5OTQ1XzFiZTM1NDcwZGY3OGQ5YTkzM2M5Nzg4M2Q2M2VlNWQwMGNmNDFhYTRfMTczMzkzODAxNg=="
API_URL = f"https://www.scorebat.com/video-api/v3/feed/?token={SCOREBAT_TOKEN}"

@app.route('/')
def index():
    return render_template('mouradaustade.html')

@app.route('/api/matches')
def get_matches():
    try:
        response = requests.get(API_URL)
        response.raise_for_status()  # Lève une exception si status code != 200
        
        data = response.json()
        matches = []
        
        for match in data.get('response', []):
            matches.append({
                'id': match.get('matchId', ''),
                'homeTeam': match.get('homeTeam', {}).get('name', ''),
                'awayTeam': match.get('awayTeam', {}).get('name', ''),
                'competition': match.get('competition', ''),
                'has_stream': True,  # Si le match est dans l'API, il a un stream
                'date': match.get('date', '')
            })
        
        return jsonify(matches)
        
    except requests.RequestException as e:
        print(f"Erreur API: {e}")
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        print(f"Erreur inattendue: {e}")
        return jsonify({'error': 'Erreur serveur'}), 500

@app.route('/stream/<match_id>')
def stream(match_id):
    return render_template('stream.html', match_id=match_id)

if __name__ == '__main__':
    app.run(debug=True)
