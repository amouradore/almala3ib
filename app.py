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

STREAM_SOURCES = ['alpha', 'bravo', 'charlie', 'delta', 'echo', 'foxtrot']

STREAM_MAPPINGS = {
    'GNK Dinamo Zagreb-Celtic': {
        'id': '19296290',
        'source': 'alpha'
    },
    'Atalanta-Real Madrid': {
        'id': '19296292',
        'source': 'bravo'
    },
    'Brest-PSV': {
        'id': '19296294',
        'source': 'charlie'
    },
    'Girona-Liverpool': {
        'id': '19296291',
        'source': 'charlie'
    },
    'Red Bull Salzburg-Paris Saint-Germain': {
        'id': '19296296',
        'source': 'charlie'
    },
    'Bayer 04 Leverkusen-Inter': {
        'id': '19296293',
        'source': 'charlie'
    },
    'RB Leipzig-Young Boys': {
        'id': '19296295',
        'source': 'charlie'
    },
    'Crvena Zvezda-Manchester City': {
        'id': '19296289',
        'source': 'charlie'
    }
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
    # Ajouter des logs pour le débogage
    app.logger.info(f"Recherche de stream pour: {team1} vs {team2}")
    
    # Normaliser les noms d'équipes
    team1_norm = normalize_team_name(team1)
    team2_norm = normalize_team_name(team2)
    
    # Log des noms normalisés
    app.logger.info(f"Noms normalisés: {team1_norm} vs {team2_norm}")
    
    possible_keys = [
        f"{team1_norm}-{team2_norm}",
        f"{team1}-{team2}",
        f"{team1_norm}-{team2}",
        f"{team1}-{team2_norm}"
    ]
    
    # Log des clés possibles
    app.logger.info(f"Clés recherchées: {possible_keys}")
    
    for key in possible_keys:
        if key in STREAM_MAPPINGS:
            stream_info = STREAM_MAPPINGS[key]
            team1_path = team1_norm.lower().replace(' ', '-')
            team2_path = team2_norm.lower().replace(' ', '-')
            url = f"https://embedme.top/embed/{stream_info['source']}/{team1_path}-vs-{team2_path}-{stream_info['id']}/1"
            app.logger.info(f"URL générée: {url}")
            return url
    
    app.logger.warning(f"Aucun stream trouvé pour {team1} vs {team2}")
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
