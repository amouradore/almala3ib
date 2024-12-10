from flask import Flask, jsonify, render_template
from flask_cors import CORS
import requests
from datetime import datetime
import time
import os

app = Flask(__name__)
CORS(app)

# Cache pour les requêtes API
CACHE_DURATION = 30  # secondes
cache = {}

STREAM_MAPPINGS = {
    'Brest-PSV': '19296294',
    'Girona-Liverpool': '19296291',
    'Red Bull Salzburg-Paris Saint-Germain': '19296296',
    'Bayer 04 Leverkusen-Inter': '19296293',
    'GNK Dinamo Zagreb-Celtic': '19296290',
    'Atalanta-Real Madrid': '19296292',
    'RB Leipzig-Young Boys': '19296295',
    'Crvena Zvezda-Manchester City': '19296289'
}

def normalize_team_name(name):
    normalizations = {
        'PSV Eindhoven': 'PSV',
        'Paris SG': 'Paris Saint-Germain',
        'Inter Milan': 'Inter',
        'Red Star Belgrade': 'Crvena Zvezda',
        'BSC Young Boys': 'Young Boys',
        # Ajoutez d'autres normalisations si nécessaire
    }
    return normalizations.get(name, name)

def get_stream_url(team1, team2):
    # Normaliser les noms d'équipes
    team1_norm = normalize_team_name(team1)
    team2_norm = normalize_team_name(team2)
    
    # Essayer différentes combinaisons de noms
    possible_keys = [
        f"{team1_norm}-{team2_norm}",
        f"{team1}-{team2}",
        f"{team1_norm}-{team2}",
        f"{team1}-{team2_norm}"
    ]
    
    for key in possible_keys:
        if key in STREAM_MAPPINGS:
            stream_id = STREAM_MAPPINGS[key]
            # Construire l'URL avec les noms normalisés pour le chemin
            team1_path = team1_norm.lower().replace(' ', '-')
            team2_path = team2_norm.lower().replace(' ', '-')
            return f"https://embedme.top/embed/charlie/{team1_path}-vs-{team2_path}-{stream_id}/1"
    
    return None

def get_cached_data(key, fetch_func):
    current_time = time.time()
    if key in cache:
        data, timestamp = cache[key]
        if current_time - timestamp < CACHE_DURATION:
            return data
    
    data = fetch_func()
    cache[key] = (data, current_time)
    return data

# Add a test route to verify the server is running
@app.route('/')
def home():
    # Remplacez le retour JSON par un template HTML
    return render_template('mouradaustade.html')

@app.route('/api/matches/<date>')
def get_matches(date):
    def fetch_matches():
        url = "http://api.football-data.org/v4/matches"
        headers = {
            'X-Auth-Token': os.environ.get('FOOTBALL_API_KEY', '3f9226033c324e538d8d34a36118390b')
        }
        
        try:
            response = requests.get(url, headers=headers)
            data = response.json()
            all_matches = []
            
            if 'matches' in data:
                for match in data['matches']:
                    team1 = match['homeTeam']['name']
                    team2 = match['awayTeam']['name']
                    stream_url = get_stream_url(team1, team2)
                    
                    match_info = {
                        'team1': team1,
                        'team2': team2,
                        'team1_logo': match['homeTeam'].get('crest', ''),
                        'team2_logo': match['awayTeam'].get('crest', ''),
                        'time': datetime.strptime(match['utcDate'], '%Y-%m-%dT%H:%M:%SZ').strftime('%H:%M'),
                        'status': match['status'],
                        'score': f"{match['score']['fullTime']['home'] if match['score']['fullTime']['home'] is not None else '-'}-{match['score']['fullTime']['away'] if match['score']['fullTime']['away'] is not None else '-'}",
                        'competition': match['competition']['name'],
                        'stream_url': stream_url,
                        'has_stream': bool(stream_url)
                    }
                    all_matches.append(match_info)
            
            return all_matches
            
        except Exception as e:
            app.logger.error(f'Error fetching matches: {str(e)}')
            return []
    
    matches = get_cached_data(f'matches_{date}', fetch_matches)
    return jsonify(matches)

@app.route('/test_api')
def test_api():
    url = "http://api.football-data.org/v4/matches"
    
    headers = {
        'X-Auth-Token': '3f9226033c324e538d8d34a36118390b'
    }
    
    try:
        response = requests.get(url, headers=headers)
        app.logger.info(f'Test API Status: {response.status_code}')
        app.logger.info(f'Test API Response: {response.text[:1000]}')
        
        return jsonify({
            'status': response.status_code,
            'data': response.json()
        })
    except Exception as e:
        return jsonify({
            'error': str(e)
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))  # Render utilise généralement le port 10000
    app.run(host='0.0.0.0', port=port)
