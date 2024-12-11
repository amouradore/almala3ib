from flask import Flask, render_template, jsonify
import requests

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('mouradaustade.html')

@app.route('/api/matches')
def get_matches():
    # URL de l'API ScoreBat avec votre token
    API_URL = "https://www.scorebat.com/video-api/v3/feed/?token=MTg5OTQ1XzFiZTM1NDcwZGY3OGQ5YTkzM2M5Nzg4M2Q2M2VlNWQwMGNmNDFhYTRfMTczMzkzODAxNg=="
    
    try:
        response = requests.get(API_URL)
        if response.ok:
            data = response.json()
            matches = []
            for match in data.get('response', []):
                matches.append({
                    'id': match.get('matchId', ''),
                    'homeTeam': match.get('homeTeam', {}).get('name', ''),
                    'awayTeam': match.get('awayTeam', {}).get('name', ''),
                    'competition': match.get('competition', ''),
                    'has_stream': bool(match.get('videos', [])),
                    'thumbnail': match.get('thumbnail', ''),
                    'date': match.get('date', '')
                })
            return jsonify(matches)
    except Exception as e:
        print(f"Erreur API: {e}")
        return jsonify([])

@app.route('/stream/<match_id>')
def stream(match_id):
    return render_template('stream.html', match_id=match_id)

if __name__ == '__main__':
    app.run(debug=True)
