import os
import sys
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.metadata import extract_metadata

def test_url():
    test_urls = [
        "https://github.com/microsoft/vscode",
        "https://www.python.org/",
    ]
    
    # Read stored metadata
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database.json')
    
    for url in test_urls:
        print("\n" + "="*50)
        print(f"Testing URL: {url}")
        print("="*50)
        
        try:
            # Extract new metadata
            print("Extracting metadata...")
            new_metadata = extract_metadata(url)
            print("\nNew metadata:")
            print(json.dumps(new_metadata, indent=2))
            
            # Show stored metadata
            with open(db_path, 'r') as f:
                stored_data = json.load(f)
                if url in stored_data:
                    print("\nStored metadata:")
                    print(json.dumps(stored_data[url], indent=2))
                    
                    # Verify metadata matches
                    if new_metadata == stored_data[url]['metadata']:
                        print("\n✅ Verification: Stored metadata matches extracted metadata")
                    else:
                        print("\n❌ Verification: Metadata mismatch!")
                
        except Exception as e:
            print(f"\n❌ Error occurred: {str(e)}")

if __name__ == "__main__":
    test_url()