from flask import Flask, jsonify, render_template, Response
from flask_cors import CORS
import requests
from datetime import datetime
import time
import os
import logging

app = Flask(__name__)
CORS(app)

# Configuration des logs au début du fichier
logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)

# Cache pour les requêtes API
CACHE_DURATION = 30  # secondes
cache = {}

STREAM_SOURCES = ['alpha', 'bravo', 'charlie', 'delta', 'echo', 'foxtrot']

STREAM_MAPPINGS = {
    'Dinamo Zagreb-Celtic': {
        'id': '19296290',
        'source': 'alpha'
    },
    'Girona-Liverpool': {
        'id': '19296291',
        'source': 'charlie'
    },
    'Atalanta-Real Madrid': {
        'id': '19296292',
        'source': 'bravo'
    },
    'Brest-PSV': {
        'id': '19296294',
        'source': 'charlie'
    },
    'Salzburg-PSG': {
        'id': '19296295',
        'source': 'delta'
    },
    'Shakhtar Donetsk-Bayern Munich': {
        'id': '19296296',
        'source': 'echo'
    },
    'Leipzig-Aston Villa': {
        'id': '19296297',
        'source': 'foxtrot'
    },
    'Club Brugge-Sporting CP': {
        'id': '19296298',
        'source': 'alpha'
    },
    'Leverkusen-Inter': {
        'id': '19296299',
        'source': 'bravo'
    }
}

def normalize_team_name(name):
    """Normalise les noms d'équipes"""
    normalizations = {
        'PSV Eindhoven': 'PSV',
        'Paris Saint-Germain FC': 'PSG',
        'FC Internazionale Milano': 'Inter',
        'FC Bayern München': 'Bayern Munich',
        'Girona FC': 'Girona',
        'Liverpool FC': 'Liverpool',
        'Atalanta BC': 'Atalanta',
        'Real Madrid CF': 'Real Madrid',
        'GNK Dinamo Zagreb': 'Dinamo Zagreb',
        'Celtic FC': 'Celtic',
        'Stade Brestois 29': 'Brest',
        'RB Leipzig': 'Leipzig',
        'FC Red Bull Salzburg': 'Salzburg',
        'Sporting Clube de Portugal': 'Sporting CP',
        'Club Brugge KV': 'Club Brugge',
        'FK Shakhtar Donetsk': 'Shakhtar Donetsk',
        'Leeds United FC': 'Leeds',
        'Middlesbrough FC': 'Middlesbrough',
        'Portsmouth FC': 'Portsmouth',
        'Norwich City FC': 'Norwich',
        'Sunderland AFC': 'Sunderland',
        'Bristol City FC': 'Bristol City',
        'Luton Town FC': 'Luton',
        'Stoke City FC': 'Stoke City',
        'Burnley FC': 'Burnley',
        'Derby County FC': 'Derby County',
        'Plymouth Argyle FC': 'Plymouth',
        'Swansea City AFC': 'Swansea',
        'Sheffield Wednesday FC': 'Sheffield Wednesday',
        'Blackburn Rovers FC': 'Blackburn',
        'Bayer 04 Leverkusen': 'Leverkusen',
        'Aston Villa FC': 'Aston Villa'
    }
    return normalizations.get(name, name)

def debug_stream_search(team1, team2):
    """Fonction auxiliaire pour le débogage des streams"""
    debug_info = {
        'original_teams': f"{team1} vs {team2}",
        'normalized_teams': f"{normalize_team_name(team1)} vs {normalize_team_name(team2)}",
        'available_mappings': list(STREAM_MAPPINGS.keys())
    }
    
    app.logger.debug(f"""
    ====== DEBUG STREAM SEARCH ======
    Original teams: {debug_info['original_teams']}
    Normalized teams: {debug_info['normalized_teams']}
    Available mappings: {debug_info['available_mappings']}
    ===============================""")
    
    return debug_info

def get_stream_url(team1, team2):
    debug_info = debug_stream_search(team1, team2)
    
    # Normaliser les noms d'équipes
    team1_norm = normalize_team_name(team1)
    team2_norm = normalize_team_name(team2)
    
    app.logger.debug(f"Normalized names: {team1_norm} vs {team2_norm}")
    
    # Créer toutes les combinaisons possibles avec les noms normalisés
    possible_keys = [
        f"{team1_norm}-{team2_norm}",
        f"{team2_norm}-{team1_norm}"
    ]
    
    app.logger.debug(f"Trying normalized keys: {possible_keys}")
    
    # Essayer toutes les combinaisons
    for key in possible_keys:
        if key in STREAM_MAPPINGS:
            stream_info = STREAM_MAPPINGS[key]
            url = f"https://embedme.top/embed/{stream_info['source']}/{team1_norm.lower().replace(' ', '-')}-vs-{team2_norm.lower().replace(' ', '-')}-{stream_info['id']}/1"
            app.logger.debug(f"Match found with key: {key}")
            app.logger.debug(f"Generated URL: {url}")
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
def index():
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
                    app.logger.debug(f"Match info: {match_info['team1']} vs {match_info['team2']}, has_stream: {match_info['has_stream']}, stream_url: {match_info['stream_url']}")
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

@app.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy.html')

@app.route('/robots.txt')
def robots():
    return """
User-agent: *
Allow: /
Sitemap: https://almala3ib.onrender.com/sitemap.xml
"""

@app.route('/sitemap.xml')
def sitemap():
    return Response("""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://almala3ib.onrender.com/</loc>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>https://almala3ib.onrender.com/privacy-policy</loc>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
</urlset>
""", mimetype='application/xml')

@app.route('/adsense-test')
def adsense_test():
    return """
    <html>
        <head>
            <title>Test AdSense</title>
            <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-9547009217122053"
             crossorigin="anonymous"></script>
        </head>
        <body>
            <h1>Test Page for AdSense</h1>
            <p>This is a test page for Google AdSense verification.</p>
        </body>
    </html>
    """

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))  # Render utilise généralement le port 10000
    app.run(host='0.0.0.0', port=port)
