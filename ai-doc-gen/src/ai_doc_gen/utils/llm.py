"""
LLM utilities for AI document generation.
Handles secure API key loading and provides functions for synonym generation and matching.
"""

import os
import json
import logging
import hashlib
import time
import tempfile
import shutil
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
try:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    logger.info("OpenAI client initialized successfully")
except ImportError:
    logger.error("openai package not installed. Run: uv add openai")
    client = None
except Exception as e:
    logger.error(f"Failed to initialize OpenAI client: {e}")
    client = None

# Import acronym expander
try:
    from .acronym_expander import AcronymExpander, create_enhanced_synonym_prompt
    ACRONYM_EXPANDER_AVAILABLE = True
except ImportError:
    logger.warning("Acronym expander not available - using basic synonym generation")
    ACRONYM_EXPANDER_AVAILABLE = False


class CachePoisoningError(Exception):
    """Raised when cache poisoning is detected."""
    pass


class LLMUtility:
    """Utility class for LLM operations with caching and error handling."""
    
    def __init__(self, cache_dir: str = "cache", cache_ttl_hours: int = 24, cache_version: str = "1.0"):
        self.cache_dir = cache_dir
        self.cache_ttl_hours = cache_ttl_hours
        self.cache_version = cache_version
        os.makedirs(cache_dir, exist_ok=True)
        # Cache hit/miss counters
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Initialize acronym expander if available
        self.acronym_expander = None
        if ACRONYM_EXPANDER_AVAILABLE:
            try:
                self.acronym_expander = AcronymExpander()
                logger.info("Acronym expander initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize acronym expander: {e}")
        
    def _validate_input(self, title: str) -> str:
        """Validate and sanitize input to prevent injection attacks."""
        if not isinstance(title, str):
            raise ValueError("Title must be a string")
        
        # Remove dangerous characters and limit length
        title = title.strip()
        if len(title) > 200:
            raise ValueError("Title too long (max 200 characters)")
        
        # Remove path traversal attempts
        dangerous_chars = ['/', '\\', '..', '~', '*', '?', '"', '<', '>', '|']
        for char in dangerous_chars:
            if char in title:
                raise ValueError(f"Dangerous character '{char}' in title")
        
        return title
    
    def _validate_synonyms(self, synonyms: List[str]) -> List[str]:
        """Validate synonym list to prevent malicious content."""
        if not isinstance(synonyms, list):
            raise CachePoisoningError("Synonyms must be a list")
        
        validated_synonyms = []
        for synonym in synonyms:
            if not isinstance(synonym, str):
                logger.warning(f"Skipping non-string synonym: {synonym}")
                continue
            
            # Sanitize each synonym
            synonym = synonym.strip()
            if len(synonym) > 100:  # Reasonable limit
                logger.warning(f"Skipping overly long synonym: {synonym[:50]}...")
                continue
            
            # Check for suspicious patterns - more comprehensive patterns
            suspicious_patterns = [
                r'<script[^>]*>',  # Script tags
                r'javascript:',     # JavaScript protocol
                r'data:',          # Data protocol
                r'vbscript:',      # VBScript protocol
                r'<iframe[^>]*>',  # Iframe tags
                r'<object[^>]*>',  # Object tags
                r'<embed[^>]*>',   # Embed tags
                r'<form[^>]*>',    # Form tags
                r'exec\s*\(',      # exec() function calls
                r'eval\s*\(',      # eval() function calls
                r'system\s*\(',    # system() function calls
                r'shell_exec\s*\(', # shell_exec() function calls
                r'rm\s+-rf',       # Dangerous rm commands
                r'delete\s+from',  # SQL injection patterns
                r'drop\s+table',   # SQL injection patterns
                r'union\s+select', # SQL injection patterns
                r'<.*?>',          # Any HTML tags
                r'&[#\w]+;',       # HTML entities
                r'%[0-9a-fA-F]{2}', # URL encoding
                r'\\x[0-9a-fA-F]{2}', # Hex encoding
                r'\\u[0-9a-fA-F]{4}', # Unicode encoding
            ]
            
            import re
            is_suspicious = False
            for pattern in suspicious_patterns:
                if re.search(pattern, synonym, re.IGNORECASE):
                    logger.warning(f"Skipping suspicious synonym: {synonym}")
                    is_suspicious = True
                    break
            
            if is_suspicious:
                continue
            
            # Additional checks for common attack patterns
            dangerous_sequences = [
                '..', '~', '|', '&', ';', '`', '$', '(', ')', '{', '}',
                'script', 'javascript', 'vbscript', 'data', 'iframe',
                'object', 'embed', 'form', 'exec', 'eval', 'system'
            ]
            
            synonym_lower = synonym.lower()
            for seq in dangerous_sequences:
                if seq in synonym_lower:
                    logger.warning(f"Skipping synonym with dangerous sequence '{seq}': {synonym}")
                    is_suspicious = True
                    break
            
            if is_suspicious:
                continue
            
            if synonym and synonym not in validated_synonyms:
                validated_synonyms.append(synonym)
        
        return validated_synonyms
    
    def _generate_cache_key(self, title: str) -> str:
        """Generate a safe cache key with hash for integrity."""
        # Create a hash of the title for the filename
        title_hash = hashlib.sha256(title.encode('utf-8')).hexdigest()[:16]
        safe_title = "".join(c for c in title.lower() if c.isalnum() or c in '_-')[:50]
        return f"synonyms_{safe_title}_{title_hash}.json"
    
    def _calculate_cache_hash(self, data: Dict[str, Any]) -> str:
        """Calculate hash of cache data for integrity checking."""
        # Create a deterministic string representation
        data_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(data_str.encode('utf-8')).hexdigest()
    
    def _is_cache_expired(self, cache_data: Dict[str, Any]) -> bool:
        """Check if cache has expired."""
        timestamp = cache_data.get('timestamp', 0)
        current_time = time.time()
        return (current_time - timestamp) > (self.cache_ttl_hours * 3600)
    
    def _load_cache_safely(self, cache_path: str) -> Optional[Dict[str, Any]]:
        """Safely load cache with integrity checks."""
        try:
            # Check file size (prevent DoS with huge files)
            if os.path.getsize(cache_path) > 1024 * 1024:  # 1MB limit
                logger.warning(f"Cache file too large: {cache_path}")
                return None
            
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Validate cache structure
            required_fields = ['title', 'synonyms', 'model', 'temperature', 'prompt', 'timestamp', 'version', 'hash']
            for field in required_fields:
                if field not in cache_data:
                    logger.warning(f"Cache missing required field: {field}")
                    return None
            
            # Check version compatibility
            if cache_data.get('version') != self.cache_version:
                logger.info(f"Cache version mismatch, regenerating: {cache_data.get('version')} vs {self.cache_version}")
                return None
            
            # Verify integrity hash
            expected_hash = cache_data.get('hash')
            if expected_hash:
                actual_hash = self._calculate_cache_hash({k: v for k, v in cache_data.items() if k != 'hash'})
                if expected_hash != actual_hash:
                    logger.warning(f"Cache integrity check failed: {cache_path}")
                    return None
            
            # Check expiration
            if self._is_cache_expired(cache_data):
                logger.info(f"Cache expired: {cache_path}")
                return None
            
            # Validate synonyms
            synonyms = self._validate_synonyms(cache_data.get('synonyms', []))
            if len(synonyms) != len(cache_data.get('synonyms', [])):
                logger.warning(f"Cache synonyms validation failed, regenerating: {cache_path}")
                return None
            
            return cache_data
            
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.warning(f"Cache file corrupted: {cache_path}, error: {e}")
            return None
        except Exception as e:
            logger.warning(f"Failed to load cache: {cache_path}, error: {e}")
            return None
    
    def _save_cache_safely(self, cache_path: str, cache_data: Dict[str, Any]) -> bool:
        """Safely save cache with atomic writes and integrity protection."""
        try:
            # Add metadata
            cache_data['timestamp'] = time.time()
            cache_data['version'] = self.cache_version
            cache_data['hash'] = self._calculate_cache_hash(cache_data)
            
            # Write to temporary file first (atomic operation)
            temp_path = cache_path + '.tmp'
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            # Atomic move
            shutil.move(temp_path, cache_path)
            return True
            
        except Exception as e:
            logger.error(f"Failed to save cache: {cache_path}, error: {e}")
            # Clean up temp file if it exists
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
            return False
    
    def _clear_poisoned_cache(self, cache_path: str):
        """Remove potentially poisoned cache file."""
        try:
            if os.path.exists(cache_path):
                os.remove(cache_path)
                logger.info(f"Removed potentially poisoned cache: {cache_path}")
        except Exception as e:
            logger.error(f"Failed to remove cache: {cache_path}, error: {e}")
    
    def get_cache_stats(self):
        """Return cache hit/miss statistics for this instance."""
        return {
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses
        }
    
    def get_synonyms_from_llm(self, title: str, model: str = "gpt-4", temperature: float = 0.2) -> List[str]:
        """
        Get synonyms and abbreviations for a section title using LLM.
        
        Args:
            title: The section title to find synonyms for
            model: The LLM model to use
            temperature: Sampling temperature for generation
            
        Returns:
            List of synonyms and abbreviations
        """
        if not client:
            logger.warning("OpenAI not available, returning empty synonyms")
            return []
        
        # Validate input
        try:
            title = self._validate_input(title)
        except ValueError as e:
            logger.error(f"Invalid input: {e}")
            return []
            
        # Check cache first
        cache_key = self._generate_cache_key(title)
        cache_path = os.path.join(self.cache_dir, cache_key)
        
        if os.path.exists(cache_path):
            cache_data = self._load_cache_safely(cache_path)
            if cache_data:
                self.cache_hits += 1
                logger.info(f"Using cached synonyms for '{title}'")
                return cache_data.get('synonyms', [])
            else:
                # Cache was poisoned or corrupted, remove it
                self._clear_poisoned_cache(cache_path)
        
        # Generate synonyms using LLM
        self.cache_misses += 1
        
        # Use enhanced prompt if acronym expander is available
        if self.acronym_expander:
            prompt = create_enhanced_synonym_prompt(title, self.acronym_expander)
            logger.info(f"Using enhanced prompt with acronym expansion for '{title}'")
        else:
            prompt = (
                f'For the documentation section title "{title}", list all common synonyms and abbreviations '
                'used in Cisco hardware documentation. Focus on technical terms, acronyms, and variations '
                'that would appear in official documentation. Return as a Python list of strings only.'
            )
        
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=200
            )
            
            content = response.choices[0].message.content
            logger.info(f"LLM response for '{title}': {content}")
            
            # Extract and validate the list from the response
            try:
                # Try to evaluate as Python list
                synonyms = eval(content)
                if isinstance(synonyms, list):
                    synonyms = [s.strip() for s in synonyms if isinstance(s, str) and s.strip()]
                else:
                    # Fallback: try to parse as JSON
                    synonyms = json.loads(content)
            except Exception as e:
                logger.warning(f"Failed to parse LLM response as list: {e}")
                # Fallback: extract words that look like synonyms
                synonyms = self._extract_synonyms_from_text(content)
            
            # Validate synonyms before caching
            validated_synonyms = self._validate_synonyms(synonyms)
            
            # Enhance with acronym synonyms if available
            if self.acronym_expander:
                acronym_synonyms = self.acronym_expander.get_acronym_synonyms(title)
                validated_synonyms.extend(acronym_synonyms)
                validated_synonyms = list(set(validated_synonyms))  # Remove duplicates
                logger.info(f"Enhanced synonyms with {len(acronym_synonyms)} acronym synonyms")
            
            # Cache the result safely
            cache_data = {
                'title': title,
                'synonyms': validated_synonyms,
                'model': model,
                'temperature': temperature,
                'prompt': prompt
            }
            
            if self._save_cache_safely(cache_path, cache_data):
                logger.info(f"Generated and cached {len(validated_synonyms)} synonyms for '{title}': {validated_synonyms}")
            else:
                logger.warning(f"Failed to cache synonyms for '{title}'")
            
            return validated_synonyms
            
        except Exception as e:
            logger.error(f"Failed to get synonyms for '{title}': {e}")
            return []
    
    def _extract_synonyms_from_text(self, text: str) -> List[str]:
        """Fallback method to extract synonyms from LLM text response."""
        import re
        synonyms = []
        # Extract quoted strings
        quoted = re.findall(r'"([^"]*)"', text)
        synonyms.extend(quoted)
        # Extract items in brackets
        bracketed = re.findall(r'\[(.*?)\]', text)
        for item in bracketed:
            items = [i.strip().strip('"\'') for i in item.split(',')]
            synonyms.extend(items)
        # If nothing found, try splitting on commas
        if not synonyms:
            for line in text.splitlines():
                if ',' in line:
                    items = [i.strip().strip('"\'') for i in line.split(',')]
                    synonyms.extend(items)
            # If still nothing, try splitting the whole text
            if not synonyms and ',' in text:
                synonyms = [i.strip().strip('"\'') for i in text.split(',')]
        # Remove empty and deduplicate
        return list({s for s in synonyms if s})
    
    def match_sections_with_llm(self, template_section: str, candidate_section: str, 
                               model: str = "gpt-4", temperature: float = 0.1) -> Dict[str, Any]:
        """
        Use LLM to determine if two sections match with reasoning.
        
        Args:
            template_section: The template section title
            candidate_section: The candidate section title
            model: The LLM model to use
            temperature: Sampling temperature for generation
            
        Returns:
            Dictionary with match result and reasoning
        """
        if not client:
            return {'match': False, 'confidence': 0.0, 'reasoning': 'OpenAI not available'}
        
        prompt = f"""
You are matching documentation sections for Cisco hardware installation guides. 

Examples:
Template: "Power over Ethernet"
Candidate: "PoE"
Match: Yes
Confidence: 0.95
Reasoning: "PoE" is the standard abbreviation for "Power over Ethernet" in networking documentation.

Template: "Rack Installation"
Candidate: "Mounting the device in a rack"
Match: Yes
Confidence: 0.85
Reasoning: The candidate describes the same process as the template, just with different wording.

Template: "Grounding Requirements"
Candidate: "Electrical Safety"
Match: Partial
Confidence: 0.60
Reasoning: "Electrical Safety" includes grounding but is broader in scope.

Template: "Power over Ethernet"
Candidate: "Network Configuration"
Match: No
Confidence: 0.10
Reasoning: These are completely different topics with no semantic overlap.

Now evaluate:
Template: "{template_section}"
Candidate: "{candidate_section}"

Respond with JSON format:
{{
    "match": "Yes/No/Partial",
    "confidence": 0.0-1.0,
    "reasoning": "explanation"
}}
"""
        
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=300
            )
            
            content = response.choices[0].message.content
            
            # Try to parse as JSON
            try:
                result = json.loads(content)
                return {
                    'match': result.get('match', 'No'),
                    'confidence': float(result.get('confidence', 0.0)),
                    'reasoning': result.get('reasoning', 'No reasoning provided')
                }
            except json.JSONDecodeError:
                # Fallback parsing
                return self._parse_match_response(content)
                
        except Exception as e:
            logger.error(f"Failed to match sections: {e}")
            return {'match': 'No', 'confidence': 0.0, 'reasoning': f'Error: {e}'}
    
    def _parse_match_response(self, text: str) -> Dict[str, Any]:
        """Fallback method to parse LLM match response."""
        import re
        # Try to extract from JSON-style or label-prefixed lines
        match_result = 'No'
        confidence = 0.0
        reasoning = 'No reasoning provided'
        # Try JSON-style first
        match_pattern = r'"match":\s*"(Yes|No|Partial)"'
        match_match = re.search(match_pattern, text, re.IGNORECASE)
        if match_match:
            match_result = match_match.group(1)
        else:
            # Try label-prefixed
            match_line = next((l for l in text.splitlines() if l.strip().lower().startswith('match:')), None)
            if match_line:
                val = match_line.split(':', 1)[-1].strip()
                if val.lower().startswith('yes'):
                    match_result = 'Yes'
                elif val.lower().startswith('partial'):
                    match_result = 'Partial'
                elif val.lower().startswith('no'):
                    match_result = 'No'
        # Confidence
        conf_pattern = r'"confidence":\s*([0-9]*\.?[0-9]+)'
        conf_match = re.search(conf_pattern, text)
        if conf_match:
            confidence = float(conf_match.group(1))
        else:
            conf_line = next((l for l in text.splitlines() if l.strip().lower().startswith('confidence:')), None)
            if conf_line:
                try:
                    confidence = float(conf_line.split(':', 1)[-1].strip())
                except Exception:
                    confidence = 0.0
        # Reasoning
        reason_pattern = r'"reasoning":\s*"([^"]*)"'
        reason_match = re.search(reason_pattern, text)
        if reason_match:
            reasoning = reason_match.group(1)
        else:
            reason_line = next((l for l in text.splitlines() if l.strip().lower().startswith('reasoning:')), None)
            if reason_line:
                reasoning = reason_line.split(':', 1)[-1].strip()
        return {
            'match': match_result,
            'confidence': confidence,
            'reasoning': reasoning
        }


# Global instance
llm_utility = LLMUtility() 