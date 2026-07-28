import requests
from cachetools import TTLCache, cached

# Cache for 1 hour, up to 100 API endpoints
cache = TTLCache(maxsize=100, ttl=3600)

class DummyLookup:
    """Wrapper to make dictionaries act like SQLAlchemy Models so templates like 'item.code' continue to work."""
    def __init__(self, code, name):
        self.code = code
        self.name = name
        
    def to_dict(self):
        return {'code': self.code, 'name': self.name}

@cached(cache)
def get_code_list(type_name: str):
    """
    Fetches master data code lists from the external API.
    Returns a list of DummyLookup objects.
    """
    url = f"http://realnexus.comit.cloud:5000/api/CodeLists/{type_name}"
    headers = {
        "accept": "text/plain",
        "x-api-key": "1"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        # The API returns a dictionary like {"CFR": "COST AND FREIGHT", ...}
        if isinstance(data, dict):
            return [DummyLookup(k, v) for k, v in data.items()]
        elif isinstance(data, list):
            # Just in case some endpoints return a list of strings
            return [DummyLookup(str(item), str(item)) for item in data]
            
    except Exception as e:
        print(f"Error fetching {type_name} from external API: {e}")
        
    return []
