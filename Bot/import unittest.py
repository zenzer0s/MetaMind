import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.metadata import extract_metadata

class TestMetadata(unittest.TestCase):
    def test_extract_metadata_valid_url(self):
        url = "https://github.com/microsoft/vscode"
        metadata = extract_metadata(url)
        
        self.assertIsNotNone(metadata)
        self.assertIn('title', metadata)
        self.assertIn('description', metadata)
        
    def test_extract_metadata_invalid_url(self):
        url = "https://invalid-url-that-does-not-exist.com"
        metadata = extract_metadata(url)
        
        self.assertIn('error', metadata)

if __name__ == '__main__':
    unittest.main()