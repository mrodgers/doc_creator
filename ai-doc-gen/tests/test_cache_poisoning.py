#!/usr/bin/env python3
"""
Tests for cache poisoning protection in LLM utility.
"""

import json
import tempfile
import unittest
import os
import time
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_doc_gen.utils.llm import LLMUtility, CachePoisoningError


class TestCachePoisoningProtection(unittest.TestCase):
    """Test cache poisoning protection mechanisms."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.llm_util = LLMUtility(cache_dir=self.temp_dir, cache_ttl_hours=1, cache_version="1.0")
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_input_validation_dangerous_chars(self):
        """Test that dangerous characters are rejected."""
        dangerous_inputs = [
            "../../../etc/passwd",
            "title<script>alert('xss')</script>",
            "title|rm -rf /",
            "title*",
            "title?",
            "title<",
            "title>",
            "title\"",
            "title~"
        ]
        
        for dangerous_input in dangerous_inputs:
            with self.assertRaises(ValueError):
                self.llm_util._validate_input(dangerous_input)
    
    def test_input_validation_length_limit(self):
        """Test that overly long titles are rejected."""
        long_title = "a" * 201  # Over 200 character limit
        with self.assertRaises(ValueError):
            self.llm_util._validate_input(long_title)
    
    def test_input_validation_valid_input(self):
        """Test that valid input passes validation."""
        valid_inputs = [
            "Power over Ethernet",
            "Rack Installation",
            "Safety Guidelines",
            "Component Description",
            "Installation Instructions"
        ]
        
        for valid_input in valid_inputs:
            result = self.llm_util._validate_input(valid_input)
            self.assertEqual(result, valid_input)
    
    def test_synonym_validation_malicious_content(self):
        """Test that malicious synonyms are filtered out."""
        malicious_synonyms = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "exec('rm -rf /')",
            "eval('malicious_code')",
            "system('dangerous_command')",
            "a" * 101  # Over 100 character limit
        ]
        
        result = self.llm_util._validate_synonyms(malicious_synonyms)
        self.assertEqual(result, [])  # All should be filtered out
    
    def test_synonym_validation_valid_content(self):
        """Test that valid synonyms pass validation."""
        valid_synonyms = [
            "PoE",
            "Power over Ethernet",
            "802.3af",
            "Rack Installation",
            "Mounting",
            "Safety Guidelines"
        ]
        
        result = self.llm_util._validate_synonyms(valid_synonyms)
        self.assertEqual(set(result), set(valid_synonyms))
    
    def test_cache_key_generation_safety(self):
        """Test that cache keys are generated safely."""
        dangerous_titles = [
            "../../../etc/passwd",
            "title<script>alert('xss')</script>",
            "title|rm -rf /",
            "title*",
            "title?"
        ]
        
        for dangerous_title in dangerous_titles:
            # Should not raise exception, should sanitize
            cache_key = self.llm_util._generate_cache_key(dangerous_title)
            self.assertIsInstance(cache_key, str)
            self.assertNotIn("..", cache_key)
            self.assertNotIn("<", cache_key)
            self.assertNotIn(">", cache_key)
            self.assertNotIn("|", cache_key)
            self.assertNotIn("*", cache_key)
            self.assertNotIn("?", cache_key)
    
    def test_cache_integrity_check(self):
        """Test that cache integrity is verified."""
        # Create valid cache data
        cache_data = {
            'title': 'Test Title',
            'synonyms': ['test', 'example'],
            'model': 'gpt-4',
            'temperature': 0.2,
            'prompt': 'test prompt'
        }
        
        # Calculate hash
        hash_value = self.llm_util._calculate_cache_hash(cache_data)
        
        # Verify hash is consistent
        hash_value2 = self.llm_util._calculate_cache_hash(cache_data)
        self.assertEqual(hash_value, hash_value2)
        
        # Verify hash changes when data changes
        cache_data['synonyms'] = ['test', 'example', 'modified']
        hash_value3 = self.llm_util._calculate_cache_hash(cache_data)
        self.assertNotEqual(hash_value, hash_value3)
    
    def test_cache_expiration(self):
        """Test that cache expiration works correctly."""
        # Create cache data with old timestamp
        cache_data = {
            'title': 'Test Title',
            'synonyms': ['test'],
            'model': 'gpt-4',
            'temperature': 0.2,
            'prompt': 'test prompt',
            'timestamp': time.time() - (2 * 3600),  # 2 hours ago
            'version': '1.0',
            'hash': 'test_hash'
        }
        
        # Should be expired
        self.assertTrue(self.llm_util._is_cache_expired(cache_data))
        
        # Create cache data with recent timestamp
        cache_data['timestamp'] = time.time() - (0.5 * 3600)  # 30 minutes ago
        
        # Should not be expired
        self.assertFalse(self.llm_util._is_cache_expired(cache_data))
    
    def test_cache_version_mismatch(self):
        """Test that cache version mismatches are detected."""
        # Create cache data with different version
        cache_data = {
            'title': 'Test Title',
            'synonyms': ['test'],
            'model': 'gpt-4',
            'temperature': 0.2,
            'prompt': 'test prompt',
            'timestamp': time.time(),
            'version': '0.9',  # Different version
            'hash': 'test_hash'
        }
        
        # Save to cache file
        cache_path = os.path.join(self.temp_dir, "test_cache.json")
        with open(cache_path, 'w') as f:
            json.dump(cache_data, f)
        
        # Should return None due to version mismatch
        result = self.llm_util._load_cache_safely(cache_path)
        self.assertIsNone(result)
    
    def test_cache_corruption_detection(self):
        """Test that corrupted cache files are detected."""
        # Create corrupted cache file
        cache_path = os.path.join(self.temp_dir, "corrupted_cache.json")
        with open(cache_path, 'w') as f:
            f.write("invalid json content")
        
        # Should return None due to corruption
        result = self.llm_util._load_cache_safely(cache_path)
        self.assertIsNone(result)
    
    def test_cache_file_size_limit(self):
        """Test that oversized cache files are rejected."""
        # Create a large cache file
        cache_path = os.path.join(self.temp_dir, "large_cache.json")
        large_data = {'data': 'x' * (2 * 1024 * 1024)}  # 2MB
        
        with open(cache_path, 'w') as f:
            json.dump(large_data, f)
        
        # Should return None due to size limit
        result = self.llm_util._load_cache_safely(cache_path)
        self.assertIsNone(result)
    
    def test_atomic_cache_write(self):
        """Test that cache writes are atomic."""
        cache_data = {
            'title': 'Test Title',
            'synonyms': ['test'],
            'model': 'gpt-4',
            'temperature': 0.2,
            'prompt': 'test prompt'
        }
        
        cache_path = os.path.join(self.temp_dir, "atomic_test.json")
        
        # Should succeed
        result = self.llm_util._save_cache_safely(cache_path, cache_data)
        self.assertTrue(result)
        
        # Verify file exists and is valid
        self.assertTrue(os.path.exists(cache_path))
        
        # Verify temp file was cleaned up
        temp_path = cache_path + '.tmp'
        self.assertFalse(os.path.exists(temp_path))
    
    def test_poisoned_cache_removal(self):
        """Test that poisoned cache files are removed."""
        cache_path = os.path.join(self.temp_dir, "poisoned_cache.json")
        
        # Create a file
        with open(cache_path, 'w') as f:
            f.write("poisoned content")
        
        # Verify file exists
        self.assertTrue(os.path.exists(cache_path))
        
        # Remove poisoned cache
        self.llm_util._clear_poisoned_cache(cache_path)
        
        # Verify file was removed
        self.assertFalse(os.path.exists(cache_path))
    
    @patch('ai_doc_gen.utils.llm.client')
    def test_end_to_end_poisoning_protection(self, mock_client):
        """Test end-to-end protection against cache poisoning."""
        # Mock LLM response with malicious content
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '["<script>alert(\'xss\')</script>", "javascript:alert(\'xss\')", "PoE", "Power over Ethernet"]'
        mock_client.chat.completions.create.return_value = mock_response
        
        # This should filter out malicious content and only return safe synonyms
        result = self.llm_util.get_synonyms_from_llm("Power over Ethernet")
        
        # Should only contain safe synonyms
        self.assertIn("PoE", result)
        self.assertIn("Power over Ethernet", result)
        self.assertNotIn("<script>alert('xss')</script>", result)
        self.assertNotIn("javascript:alert('xss')", result)


if __name__ == '__main__':
    unittest.main() 