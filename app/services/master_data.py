import requests
import os
import json
import time

CACHE_FILE_PATH = os.path.join(os.path.dirname(__file__), 'master_data_cache.json')
CACHE_TTL = 3600  # 1 hour in seconds

class DummyLookup:
    """Wrapper to make dictionaries act like SQLAlchemy Models so templates like 'item.code' continue to work."""
    def __init__(self, code, name):
        self.code = code
        self.name = name
        
    def to_dict(self):
        return {'code': self.code, 'name': self.name}

def _load_cache():
    if os.path.exists(CACHE_FILE_PATH):
        try:
            with open(CACHE_FILE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to read master data cache file: {e}")
    return {}

def _write_cache(cache_data):
    try:
        # Write via a temp file to ensure atomic updates and prevent corruption across concurrent workers
        temp_path = CACHE_FILE_PATH + '.tmp'
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        os.replace(temp_path, CACHE_FILE_PATH)
    except Exception as e:
        print(f"Failed to write master data cache file: {e}")

def get_code_list(type_name: str):
    """
    Fetches master data code lists from local persistent JSON cache or external API.
    Returns a list of DummyLookup objects.
    """
    now = time.time()
    cache_data = _load_cache()
    
    # Check if we have cached data
    if type_name in cache_data:
        entry = cache_data[type_name]
        timestamp = entry.get('timestamp', 0)
        data = entry.get('data', [])
        
        # If cache is not expired, return it immediately
        if now - timestamp < CACHE_TTL:
            return [DummyLookup(item['code'], item['name']) for item in data]
            
    # Cache expired or missing -> fetch from external API
    url = f"http://realnexus.comit.cloud:5000/api/CodeLists/{type_name}"
    headers = {
        "accept": "text/plain",
        "x-api-key": "1"
    }
    
    fetched_list = []
    success = False
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, dict):
            fetched_list = [{'code': k, 'name': v} for k, v in data.items()]
            success = True
        elif isinstance(data, list):
            fetched_list = [{'code': str(item), 'name': str(item)} for item in data]
            success = True
            
    except Exception as e:
        print(f"Error fetching {type_name} from external API: {e}")
        
    if success:
        # Save to cache
        cache_data[type_name] = {
            'timestamp': now,
            'data': fetched_list
        }
        _write_cache(cache_data)
        return [DummyLookup(item['code'], item['name']) for item in fetched_list]
    else:
        # Fallback to expired cache if API request fails, ensuring high availability
        if type_name in cache_data:
            print(f"API failed. Falling back to expired cache for {type_name}")
            data = cache_data[type_name].get('data', [])
            return [DummyLookup(item['code'], item['name']) for item in data]
            
    return []
