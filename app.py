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
    app.logger.info(f'Fetching matches for date: {date}')
    
    def fetch_matches():
        url = "http://api.football-data.org/v4/matches"
        
        headers = {
            'X-Auth-Token': '3f9226033c324e538d8d34a36118390b'
        }
        
        try:
            response = requests.get(url, headers=headers)
            app.logger.info(f'API Response Status: {response.status_code}')
            
            data = response.json()
            app.logger.info(f'API Response Data: {data}')
            
            all_matches = []
            if 'matches' in data:
                for match in data['matches']:
                    match_info = {
                        'team1': match['homeTeam']['name'],
                        'team2': match['awayTeam']['name'],
                        'team1_logo': match['homeTeam'].get('crest', ''),
                        'team2_logo': match['awayTeam'].get('crest', ''),
                        'time': datetime.strptime(match['utcDate'], '%Y-%m-%dT%H:%M:%SZ').strftime('%H:%M'),
                        'status': match['status'],
                        'score': f"{match['score']['fullTime']['home'] if match['score']['fullTime']['home'] is not None else '-'}-{match['score']['fullTime']['away'] if match['score']['fullTime']['away'] is not None else '-'}",
                        'competition': match['competition']['name'],
                        'stats': {
                            'possession': {
                                'home': '0',
                                'away': '0'
                            },
                            'shots': {
                                'home': '0',
                                'away': '0'
                            }
                        }
                    }
                    all_matches.append(match_info)
            
            app.logger.info(f'Processed {len(all_matches)} matches')
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
