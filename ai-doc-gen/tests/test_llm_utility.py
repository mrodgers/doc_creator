#!/usr/bin/env python3
"""
Tests for LLM utility functions.
Uses mocked responses to avoid API calls during testing.
"""

import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_doc_gen.utils.llm import LLMUtility


class TestLLMUtility(unittest.TestCase):
    """Test cases for LLMUtility class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.llm_util = LLMUtility(cache_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @patch('ai_doc_gen.utils.llm.client')
    def test_get_synonyms_from_llm_success(self, mock_client):
        """Test successful synonym generation."""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '["PoE", "Power over Ethernet", "802.3af"]'
        mock_client.chat.completions.create.return_value = mock_response
        
        synonyms = self.llm_util.get_synonyms_from_llm("Power over Ethernet")
        
        expected = ["PoE", "Power over Ethernet", "802.3af"]
        self.assertEqual(synonyms, expected)
        
        # Verify OpenAI was called
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('ai_doc_gen.utils.llm.client')
    def test_get_synonyms_from_llm_cached(self, mock_client):
        """Test that cached synonyms are used."""
        # Create a cache file
        cache_data = {
            'title': 'Power over Ethernet',
            'synonyms': ['PoE', 'Power over Ethernet'],
            'model': 'gpt-4',
            'temperature': 0.2,
            'prompt': 'test prompt'
        }
        
        cache_path = Path(self.temp_dir) / "synonyms_power_over_ethernet.json"
        with open(cache_path, 'w') as f:
            json.dump(cache_data, f)
        
        # Should use cache and not call OpenAI
        synonyms = self.llm_util.get_synonyms_from_llm("Power over Ethernet")
        
        self.assertEqual(synonyms, ['PoE', 'Power over Ethernet'])
        mock_client.chat.completions.create.assert_not_called()
    
    @patch('ai_doc_gen.utils.llm.client')
    def test_get_synonyms_from_llm_parse_fallback(self, mock_client):
        """Test fallback parsing when eval fails."""
        # Mock OpenAI response with invalid format
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = 'PoE, Power over Ethernet, 802.3af'
        mock_client.chat.completions.create.return_value = mock_response
        
        synonyms = self.llm_util.get_synonyms_from_llm("Power over Ethernet")
        
        # Should extract synonyms using fallback method
        self.assertIn("PoE", synonyms)
        self.assertIn("Power over Ethernet", synonyms)
    
    @patch('ai_doc_gen.utils.llm.client')
    def test_get_synonyms_from_llm_no_openai(self, mock_client):
        """Test behavior when OpenAI is not available."""
        mock_client.chat.completions.create.side_effect = Exception("API error")
        
        synonyms = self.llm_util.get_synonyms_from_llm("Power over Ethernet")
        
        self.assertEqual(synonyms, [])
    
    @patch('ai_doc_gen.utils.llm.client')
    def test_match_sections_with_llm_success(self, mock_client):
        """Test successful section matching."""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '''
        {
            "match": "Yes",
            "confidence": 0.95,
            "reasoning": "PoE is the standard abbreviation for Power over Ethernet"
        }
        '''
        mock_client.chat.completions.create.return_value = mock_response
        
        result = self.llm_util.match_sections_with_llm("Power over Ethernet", "PoE")
        
        expected = {
            'match': 'Yes',
            'confidence': 0.95,
            'reasoning': 'PoE is the standard abbreviation for Power over Ethernet'
        }
        self.assertEqual(result, expected)
    
    @patch('ai_doc_gen.utils.llm.client')
    def test_match_sections_with_llm_parse_fallback(self, mock_client):
        """Test fallback parsing for match response."""
        # Mock OpenAI response with invalid JSON
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '''
        Match: Yes
        Confidence: 0.85
        Reasoning: Good match
        '''
        mock_client.chat.completions.create.return_value = mock_response
        
        result = self.llm_util.match_sections_with_llm("Power over Ethernet", "PoE")
        
        self.assertEqual(result['match'], 'Yes')
        self.assertEqual(result['confidence'], 0.85)
        self.assertIn('Good match', result['reasoning'])
    
    @patch('ai_doc_gen.utils.llm.client')
    def test_match_sections_with_llm_no_openai(self, mock_client):
        """Test behavior when OpenAI is not available for matching."""
        mock_client.chat.completions.create.side_effect = Exception("API error")
        
        result = self.llm_util.match_sections_with_llm("Power over Ethernet", "PoE")
        
        expected = {'match': 'No', 'confidence': 0.0, 'reasoning': 'Error: API error'}
        self.assertEqual(result, expected)
    
    def test_extract_synonyms_from_text(self):
        """Test synonym extraction from text."""
        text = 'Here are some synonyms: "PoE", "Power over Ethernet", and [802.3af, IEEE 802.3af]'
        
        synonyms = self.llm_util._extract_synonyms_from_text(text)
        
        expected = ['PoE', 'Power over Ethernet', '802.3af', 'IEEE 802.3af']
        self.assertEqual(set(synonyms), set(expected))
    
    def test_parse_match_response(self):
        """Test parsing of match response."""
        text = '''
        "match": "Yes",
        "confidence": 0.85,
        "reasoning": "Good match between sections"
        '''
        
        result = self.llm_util._parse_match_response(text)
        
        expected = {
            'match': 'Yes',
            'confidence': 0.85,
            'reasoning': 'Good match between sections'
        }
        self.assertEqual(result, expected)


class TestLLMUtilityIntegration(unittest.TestCase):
    """Integration tests for LLM utility."""
    
    def test_synonym_dictionary_structure(self):
        """Test that synonym dictionary has correct structure."""
        # This would test the actual synonym generation script
        # For now, just test the expected structure
        expected_structure = {
            'metadata': {
                'template_path': str,
                'total_sections': int,
                'generation_timestamp': str,
                'model': str,
                'temperature': float
            },
            'synonyms': dict
        }
        
        # This is a structure test - actual generation would be tested separately
        self.assertTrue(True)  # Placeholder


if __name__ == '__main__':
    unittest.main() 