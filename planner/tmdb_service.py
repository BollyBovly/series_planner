import requests
from decouple import config
from .models import Series

TMDB_API_KEY = config('TMDB_API_KEY', default='')
BASE_URL = 'https://api.themoviedb.org/3'


def search_series(query):
    if not TMDB_API_KEY:
        return []
    
    url = f'{BASE_URL}/search/tv'
    params = {
        'api_key': TMDB_API_KEY,
        'query': query,
        'language': 'ru-RU'
    }
    
    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        return response.json().get('results', [])
    except Exception as e:
        print(f"TMDB API Error: {e}")
        return []


def get_series_details(tmdb_id):
    if not TMDB_API_KEY:
        return None
    
    url = f'{BASE_URL}/tv/{tmdb_id}'
    params = {
        'api_key': TMDB_API_KEY,
        'language': 'ru-RU'
    }
    
    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"TMDB API Error: {e}")
        return None


def import_from_tmdb(tmdb_id):
    data = get_series_details(tmdb_id)
    
    if not data:
        return None
    
    title = data.get('name', 'Unknown')
    description = data.get('overview', '')
    seasons = data.get('number_of_seasons', 1)
    total_episodes = data.get('number_of_episodes', 0)
    
    episode_run_time = data.get('episode_run_time', [])
    avg_duration = episode_run_time[0] if episode_run_time else 45
    
    genres = ', '.join([g['name'] for g in data.get('genres', [])])
    
    first_air_date = data.get('first_air_date', '')
    release_year = int(first_air_date[:4]) if first_air_date else None
    
    poster_path = data.get('poster_path')
    poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
    
    rating = data.get('vote_average')
    
    series, created = Series.objects.update_or_create(
        tmdb_id=tmdb_id,
        defaults={
            'title': title,
            'description': description,
            'total_seasons': seasons,
            'total_episodes': total_episodes,
            'average_episode_duration': avg_duration,
            'genres': genres,
            'release_year': release_year,
            'poster_url': poster_url,
            'rating': rating,
        }
    )
    
    return series
