from flask import Flask, render_template, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

# Configuration de l'API
API_BASE_URL = "https://api.sofascore.com/api/v1"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.sofascore.com/',
    'Origin': 'https://www.sofascore.com'
}

@app.route('/')
def index():
    return render_template('mouradaustade.html')

@app.route('/api/matches')
def get_matches():
    try:
        # Obtenir la date d'aujourd'hui au format YYYY-MM-DD
        today = datetime.now().strftime('%Y-%m-%d')
        url = f"{API_BASE_URL}/sport/football/scheduled-events/{today}"
        
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        
        data = response.json()
        matches = []
        
        for event in data.get('events', []):
            match = {
                'id': event.get('id'),
                'homeTeam': event.get('homeTeam', {}).get('name'),
                'awayTeam': event.get('awayTeam', {}).get('name'),
                'competition': event.get('tournament', {}).get('name'),
                'time': datetime.fromtimestamp(event.get('startTimestamp')).strftime('%H:%M'),
                'status': event.get('status', {}).get('description'),
                'has_stream': True  # Par défaut, on considère que tous les matches ont un stream
            }
            matches.append(match)
        
        return jsonify(matches)
        
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stream/<match_id>')
def stream(match_id):
    return render_template('stream.html', match_id=match_id)

if __name__ == '__main__':
    app.run(debug=True)
