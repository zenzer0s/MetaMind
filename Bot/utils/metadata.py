import requests
import sys
import os
from bs4 import BeautifulSoup
import json
from datetime import datetime

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

def extract_metadata(url):
    """Extract metadata from a given URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        metadata = {
            'title': soup.title.string.strip() if soup.title else '',
            'description': soup.find('meta', {'name': 'description'})['content'].strip() 
                         if soup.find('meta', {'name': 'description'}) else ''
        }
        
        # Store metadata in database.json
        store_metadata(url, metadata)
        
        return metadata
        
    except Exception as e:
        return {'error': str(e)}

def store_metadata(url, metadata):
    """Store metadata in database.json."""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database.json')
    
    try:
        with open(db_path, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}
    
    data[url] = {
        'metadata': metadata,
        'timestamp': datetime.now().isoformat()
    }
    
    with open(db_path, 'w') as f:
        json.dump(data, f, indent=4)
