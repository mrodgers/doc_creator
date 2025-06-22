#!/usr/bin/env python3
"""
Adaptive LLM Matcher with Self-Evaluation and Prompt Evolution

This module implements a step-by-step approach where:
1. LLM performs initial matching
2. LLM evaluates its own performance
3. LLM suggests prompt improvements
4. System evolves prompts based on feedback
"""

import json
import os
import time
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import openai
from dataclasses import dataclass, asdict

from src.ai_doc_gen.input_processing.document_parser import PDFParser, DOCXParser, HTMLParser, ParsedDocument


@dataclass
class MatchResult:
    """Structured result of a section match."""
    doc_section_id: int
    template_section_id: int
    confidence: float
    reasoning: str
    doc_section: str
    template_section: str
    template_source: str


@dataclass
class EvaluationResult:
    """Result of LLM self-evaluation."""
    overall_score: float
    confidence_issues: List[str]
    reasoning_issues: List[str]
    coverage_issues: List[str]
    prompt_suggestions: List[str]
    specific_improvements: List[str]


@dataclass
class PromptEvolution:
    """Tracks prompt evolution over time."""
    version: str
    timestamp: str
    changes: List[str]
    performance_metrics: Dict[str, float]
    prompt_text: str
    cost_tracking: Dict[str, Any]
    provenance: Dict[str, Any]


@dataclass
class CostTracking:
    """Tracks API costs and usage."""
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    api_calls: int = 0
    model_used: str = "gpt-4o-mini"
    timestamp: str = ""


class SafetyValidator:
    """Validates inputs and prevents processing of invalid data."""
    
    @staticmethod
    def is_valid_string(text: str) -> bool:
        """Check if string is valid and not empty/null."""
        if not text or not isinstance(text, str):
            return False
        
        # Remove whitespace and check if empty
        cleaned = text.strip()
        if not cleaned:
            return False
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'^\s*["\']\s*$',  # Just quotes
            r'^\s*[{}[\]]\s*$',  # Just brackets
            r'^\s*[,\s]+\s*$',  # Just commas/whitespace
            r'^\s*null\s*$',  # Just "null"
            r'^\s*undefined\s*$',  # Just "undefined"
            r'^\s*\\n\s*$',  # Just newlines
            r'^\s*["\']\s*\\n\s*["\']\s*$',  # Newlines in quotes
        ]
        
        for pattern in suspicious_patterns:
            if re.match(pattern, cleaned, re.IGNORECASE):
                return False
        
        # Check for minimum meaningful length
        if len(cleaned) < 2:
            return False
        
        return True
    
    @staticmethod
    def sanitize_string(text: str) -> str:
        """Sanitize string by removing problematic characters."""
        if not text:
            return ""
        
        # Remove null bytes and control characters
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    @staticmethod
    def validate_section_data(section: Dict[str, Any]) -> bool:
        """Validate section data structure."""
        required_fields = ['heading', 'content_preview']
        
        for field in required_fields:
            if field not in section:
                return False
            
            if not SafetyValidator.is_valid_string(str(section[field])):
                return False
        
        return True
    
    @staticmethod
    def validate_llm_response(response: str) -> bool:
        """Validate LLM response for suspicious patterns."""
        if not SafetyValidator.is_valid_string(response):
            return False
        
        # Check for common error patterns
        error_patterns = [
            r'LLM matching failed',
            r'Error parsing',
            r'Failed to parse',
            r'Invalid response',
            r'JSON parse error',
            r'^\s*["\']\s*\\n\s*["\']\s*$',  # Just newlines in quotes
        ]
        
        for pattern in error_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                return False
        
        return True


class AdaptiveLLMMatcher:
    """Adaptive LLM matcher with self-evaluation and prompt evolution."""
    
    def __init__(self, template_path: str, api_key: Optional[str] = None):
        self.template_path = template_path
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = openai.OpenAI(api_key=self.api_key)
        
        # Load template
        self.template = self._load_template(template_path)
        
        # Initialize parsers
        self.parsers = {
            'pdf': PDFParser(),
            'docx': DOCXParser(),
            'html': HTMLParser()
        }
        
        # Prompt evolution tracking
        self.prompt_history: List[PromptEvolution] = []
        self.current_prompt_version = "1.0"
        
        # Cost tracking
        self.cost_tracker = CostTracking()
        
        # Load or create base prompt
        self.base_prompt = self._load_or_create_base_prompt()
        
    def _load_template(self, template_path: str) -> Dict[str, Any]:
        """Load the template JSON file."""
        try:
            with open(template_path, 'r') as f:
                template = json.load(f)
            print(f"✅ Loaded template: {template.get('title', 'Unknown')}")
            return template
        except Exception as e:
            print(f"❌ Error loading template: {e}")
            return {}
    
    def _load_or_create_base_prompt(self) -> str:
        """Load existing prompt or create base prompt."""
        prompt_file = "adaptive_prompt_history.json"
        
        if Path(prompt_file).exists():
            try:
                with open(prompt_file, 'r') as f:
                    history = json.load(f)
                    if history.get('prompts'):
                        latest = history['prompts'][-1]
                        self.current_prompt_version = latest['version']
                        return latest['prompt_text']
            except Exception as e:
                print(f"⚠️  Error loading prompt history: {e}")
        
        # Create base prompt
        return self._create_base_prompt()
    
    def _create_base_prompt(self) -> str:
        """Create the initial base prompt."""
        return """You are an expert technical documentation analyst specializing in semantic section matching.

Your task is to match document sections to template sections based on semantic similarity and content purpose.

ANALYSIS CRITERIA:
1. Content Purpose: What is the main intent of this section? (installation, safety, specifications, etc.)
2. Technical Domain: What technical area does this cover? (hardware, software, procedures, etc.)
3. Content Type: Is this procedural, descriptive, reference, or requirements content?
4. Semantic Similarity: Do the sections cover the same concepts, even if titles differ?

MATCHING GUIDELINES:
- Focus on content meaning, not just title similarity
- Consider synonyms and related terms (e.g., "Installation" ≈ "Setup" ≈ "Deployment")
- Match procedural content to procedural templates
- Match reference content to reference templates
- Provide detailed reasoning for each match
- Only match if confidence > 0.6

RESPONSE FORMAT:
Return a JSON array of matches with this exact structure:
[
  {
    "doc_section_id": 0,
    "template_section_id": 5,
    "confidence": 0.9,
    "reasoning": "Detailed explanation of why these sections match semantically"
  }
]

DOCUMENT SECTIONS:
{doc_sections_text}

TEMPLATE SECTIONS:
{template_sections_text}

Analyze each document section and provide matches with detailed reasoning."""
    
    def _track_api_cost(self, response, model: str = "gpt-4o-mini"):
        """Track API usage and costs."""
        try:
            # Update cost tracking
            self.cost_tracker.api_calls += 1
            self.cost_tracker.model_used = model
            self.cost_tracker.timestamp = datetime.now().isoformat()
            
            # Calculate tokens and cost (approximate)
            if hasattr(response, 'usage'):
                self.cost_tracker.total_tokens += response.usage.total_tokens
                
                # Approximate cost calculation (gpt-4o-mini pricing)
                if model == "gpt-4o-mini":
                    # $0.00015 per 1K input tokens, $0.0006 per 1K output tokens
                    input_cost = (response.usage.prompt_tokens / 1000) * 0.00015
                    output_cost = (response.usage.completion_tokens / 1000) * 0.0006
                    self.cost_tracker.total_cost_usd += input_cost + output_cost
            
        except Exception as e:
            print(f"⚠️  Error tracking API cost: {e}")
    
    def analyze_document_adaptive(self, document_path: str) -> Dict[str, Any]:
        """Perform adaptive analysis with self-evaluation and prompt evolution."""
        print(f"🔍 Adaptive analysis: {document_path}")
        
        # Step 1: Parse document
        parsed_doc = self._parse_document(document_path)
        if not parsed_doc:
            return {'error': 'Failed to parse document'}
        
        # Step 2: Prepare section data with safety validation
        doc_sections = self._prepare_document_sections(parsed_doc)
        template_sections = self._prepare_template_sections()
        
        # Validate sections
        if not self._validate_sections(doc_sections, template_sections):
            return {'error': 'Invalid section data detected'}
        
        # Step 3: Initial LLM matching
        print("   🤖 Step 1: Initial LLM matching...")
        initial_matches = self._perform_llm_matching(doc_sections, template_sections)
        
        # Step 4: Self-evaluation
        print("   🔍 Step 2: LLM self-evaluation...")
        evaluation = self._evaluate_matching_performance(
            initial_matches, doc_sections, template_sections
        )
        
        # Step 5: Prompt improvement suggestions
        print("   💡 Step 3: Generating prompt improvements...")
        improvements = self._generate_prompt_improvements(evaluation, initial_matches)
        
        # Step 6: Evolve prompt if needed
        if improvements['should_evolve']:
            print("   🚀 Step 4: Evolving prompt...")
            self._evolve_prompt(improvements['suggestions'], evaluation)
        
        # Step 7: Re-run with evolved prompt if changed
        final_matches = initial_matches
        if improvements['should_evolve']:
            print("   🔄 Step 5: Re-running with evolved prompt...")
            final_matches = self._perform_llm_matching(doc_sections, template_sections)
        
        # Step 8: Compile results
        results = self._compile_adaptive_results(
            parsed_doc, final_matches, evaluation, improvements
        )
        
        return results
    
    def _validate_sections(self, doc_sections: List[Dict], template_sections: List[Dict]) -> bool:
        """Validate all sections for safety."""
        try:
            # Validate document sections
            for i, section in enumerate(doc_sections):
                if not SafetyValidator.validate_section_data(section):
                    print(f"   ⚠️  Invalid document section {i}: {section}")
                    return False
            
            # Validate template sections
            for i, section in enumerate(template_sections):
                if not SafetyValidator.validate_section_data(section):
                    print(f"   ⚠️  Invalid template section {i}: {section}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"   ❌ Section validation failed: {e}")
            return False
    
    def _parse_document(self, document_path: str) -> Optional[ParsedDocument]:
        """Parse document using appropriate parser."""
        try:
            doc_type = self._get_document_type(document_path)
            parser = self.parsers.get(doc_type)
            
            if not parser:
                print(f"❌ No parser available for {doc_type}")
                return None
            
            parsed_doc = parser.parse(document_path)
            print(f"   ✅ Parsed: {len(parsed_doc.sections)} sections")
            return parsed_doc
            
        except Exception as e:
            print(f"❌ Error parsing document: {e}")
            return None
    
    def _get_document_type(self, file_path: str) -> str:
        """Determine document type from file extension."""
        ext = Path(file_path).suffix.lower()
        if ext == '.pdf':
            return 'pdf'
        elif ext == '.docx':
            return 'docx'
        elif ext in ['.html', '.htm']:
            return 'html'
        else:
            return 'txt'
    
    def _prepare_document_sections(self, parsed_doc: ParsedDocument) -> List[Dict]:
        """Prepare document sections for LLM analysis with safety validation."""
        sections = []
        for i, section in enumerate(parsed_doc.sections):
            # Get content preview (first 200 characters)
            content = section.get('content', [])
            if isinstance(content, list):
                content_text = ' '.join(content)
            else:
                content_text = str(content)
            
            # Sanitize content
            content_text = SafetyValidator.sanitize_string(content_text)
            content_preview = content_text[:200] + "..." if len(content_text) > 200 else content_text
            
            # Validate heading
            heading = SafetyValidator.sanitize_string(section.get('heading', ''))
            if not SafetyValidator.is_valid_string(heading):
                heading = f"Section {i}"  # Fallback heading
            
            sections.append({
                'id': i,
                'heading': heading,
                'content_preview': content_preview,
                'content_length': len(content_text),
                'level': section.get('level', 1)
            })
        return sections
    
    def _prepare_template_sections(self) -> List[Dict]:
        """Prepare template sections for LLM analysis with safety validation."""
        sections = []
        template_sections = self.template.get('sections', [])
        
        for i, section in enumerate(template_sections):
            # Sanitize title
            title = SafetyValidator.sanitize_string(section.get('title', ''))
            if not SafetyValidator.is_valid_string(title):
                title = f"Template Section {i}"  # Fallback title
            
            sections.append({
                'id': i,
                'title': title,
                'recommended_source': section.get('recommended_source', 'unknown'),
                'content_type': section.get('content_type', 'unknown'),
                'priority': section.get('priority', 'medium')
            })
        return sections
    
    def _perform_llm_matching(self, doc_sections: List[Dict], template_sections: List[Dict]) -> List[MatchResult]:
        """Perform LLM-based section matching with safety validation."""
        try:
            # Create prompt with current version
            prompt = self._create_matching_prompt(doc_sections, template_sections)
            
            # Validate prompt
            if not SafetyValidator.is_valid_string(prompt):
                print(f"   ❌ Invalid prompt generated")
                return []
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=3000
            )
            
            # Track API cost
            self._track_api_cost(response)
            
            llm_response = response.choices[0].message.content
            
            # Validate LLM response
            if not SafetyValidator.validate_llm_response(llm_response):
                print(f"   ❌ Invalid LLM response detected: {llm_response[:100]}...")
                return []
            
            matches = self._parse_matching_response(llm_response, doc_sections, template_sections)
            
            return matches
            
        except Exception as e:
            print(f"   ❌ LLM matching failed: {e}")
            return []
    
    def _create_matching_prompt(self, doc_sections: List[Dict], template_sections: List[Dict]) -> str:
        """Create the current version of the matching prompt."""
        doc_sections_text = "\n".join([
            f"Doc Section {s['id']}: '{s['heading']}' (Content: {s['content_preview']})"
            for s in doc_sections
        ])
        
        template_sections_text = "\n".join([
            f"Template Section {s['id']}: '{s['title']}' (Type: {s['content_type']}, Source: {s['recommended_source']})"
            for s in template_sections
        ])
        
        return self.base_prompt.format(
            doc_sections_text=doc_sections_text,
            template_sections_text=template_sections_text
        )
    
    def _parse_matching_response(self, response: str, doc_sections: List[Dict], template_sections: List[Dict]) -> List[MatchResult]:
        """Parse LLM response into structured matches with safety validation."""
        try:
            # Extract JSON from response
            if '{' in response and '}' in response:
                start = response.find('[')
                end = response.rfind(']') + 1
                if start != -1 and end != -1:
                    json_str = response[start:end]
                    matches_data = json.loads(json_str)
                    
                    matches = []
                    for match_data in matches_data:
                        doc_id = match_data.get('doc_section_id')
                        template_id = match_data.get('template_section_id')
                        
                        # Validate IDs
                        if (doc_id is None or template_id is None or
                            doc_id < 0 or template_id < 0 or
                            doc_id >= len(doc_sections) or 
                            template_id >= len(template_sections)):
                            continue
                        
                        # Validate confidence
                        confidence = match_data.get('confidence', 0.0)
                        if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
                            confidence = 0.5  # Default confidence
                        
                        # Validate reasoning
                        reasoning = SafetyValidator.sanitize_string(match_data.get('reasoning', ''))
                        if not SafetyValidator.is_valid_string(reasoning):
                            reasoning = "Match based on semantic similarity"
                        
                        matches.append(MatchResult(
                            doc_section_id=doc_id,
                            template_section_id=template_id,
                            confidence=confidence,
                            reasoning=reasoning,
                            doc_section=doc_sections[doc_id]['heading'],
                            template_section=template_sections[template_id]['title'],
                            template_source=template_sections[template_id]['recommended_source']
                        ))
                    
                    return matches
            
            return []
            
        except Exception as e:
            print(f"   ⚠️  Error parsing LLM response: {e}")
            return []
    
    def _evaluate_matching_performance(self, matches: List[MatchResult], doc_sections: List[Dict], template_sections: List[Dict]) -> EvaluationResult:
        """LLM evaluates its own matching performance with safety validation."""
        try:
            # Prepare evaluation context
            match_summary = []
            for match in matches:
                match_summary.append({
                    'doc_section': match.doc_section,
                    'template_section': match.template_section,
                    'confidence': match.confidence,
                    'reasoning': match.reasoning
                })
            
            evaluation_prompt = f"""
You are an expert evaluator of semantic matching performance. Analyze the following matching results and identify areas for improvement.

MATCHING RESULTS:
{json.dumps(match_summary, indent=2)}

DOCUMENT SECTIONS COUNT: {len(doc_sections)}
TEMPLATE SECTIONS COUNT: {len(template_sections)}
MATCHES FOUND: {len(matches)}
COVERAGE: {len(matches) / len(template_sections) * 100:.1f}% if template_sections else 0

EVALUATION CRITERIA:
1. Coverage: Are important template sections being matched?
2. Confidence: Are confidence scores appropriate and well-justified?
3. Reasoning: Are the reasoning explanations detailed and accurate?
4. Semantic Accuracy: Are the matches semantically correct?

Provide your evaluation as JSON with these fields:
- overall_score: 0-100 rating of matching quality
- confidence_issues: List of specific confidence problems
- reasoning_issues: List of reasoning quality problems  
- coverage_issues: List of coverage problems
- prompt_suggestions: List of specific prompt improvements
- specific_improvements: List of actionable improvements
"""
            
            # Validate evaluation prompt
            if not SafetyValidator.is_valid_string(evaluation_prompt):
                print(f"   ❌ Invalid evaluation prompt")
                return self._create_default_evaluation()
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": evaluation_prompt}],
                temperature=0.1,
                max_tokens=2000
            )
            
            # Track API cost
            self._track_api_cost(response)
            
            evaluation_text = response.choices[0].message.content
            
            # Validate evaluation response
            if not SafetyValidator.validate_llm_response(evaluation_text):
                print(f"   ❌ Invalid evaluation response")
                return self._create_default_evaluation()
            
            evaluation_data = self._parse_evaluation_response(evaluation_text)
            
            return EvaluationResult(**evaluation_data)
            
        except Exception as e:
            print(f"   ❌ Self-evaluation failed: {e}")
            return self._create_default_evaluation()
    
    def _create_default_evaluation(self) -> EvaluationResult:
        """Create default evaluation when evaluation fails."""
        return EvaluationResult(
            overall_score=50.0,
            confidence_issues=["Evaluation failed"],
            reasoning_issues=[],
            coverage_issues=[],
            prompt_suggestions=[],
            specific_improvements=[]
        )
    
    def _parse_evaluation_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM evaluation response with safety validation."""
        try:
            if '{' in response and '}' in response:
                start = response.find('{')
                end = response.rfind('}') + 1
                if start != -1 and end != -1:
                    json_str = response[start:end]
                    data = json.loads(json_str)
                    
                    # Validate and sanitize data
                    return {
                        'overall_score': min(max(float(data.get('overall_score', 50.0)), 0.0), 100.0),
                        'confidence_issues': [SafetyValidator.sanitize_string(issue) for issue in data.get('confidence_issues', [])],
                        'reasoning_issues': [SafetyValidator.sanitize_string(issue) for issue in data.get('reasoning_issues', [])],
                        'coverage_issues': [SafetyValidator.sanitize_string(issue) for issue in data.get('coverage_issues', [])],
                        'prompt_suggestions': [SafetyValidator.sanitize_string(suggestion) for suggestion in data.get('prompt_suggestions', [])],
                        'specific_improvements': [SafetyValidator.sanitize_string(improvement) for improvement in data.get('specific_improvements', [])]
                    }
        except Exception as e:
            print(f"   ⚠️  Error parsing evaluation: {e}")
        
        # Default response
        return {
            'overall_score': 50.0,
            'confidence_issues': [],
            'reasoning_issues': [],
            'coverage_issues': [],
            'prompt_suggestions': [],
            'specific_improvements': []
        }
    
    def _generate_prompt_improvements(self, evaluation: EvaluationResult, matches: List[MatchResult]) -> Dict[str, Any]:
        """Generate prompt improvement suggestions based on evaluation."""
        try:
            improvement_prompt = f"""
Based on the following evaluation of matching performance, suggest specific improvements to the matching prompt.

EVALUATION:
Overall Score: {evaluation.overall_score}/100
Confidence Issues: {evaluation.confidence_issues}
Reasoning Issues: {evaluation.reasoning_issues}
Coverage Issues: {evaluation.coverage_issues}

CURRENT PROMPT:
{self.base_prompt}

Provide your suggestions as JSON with these fields:
- should_evolve: boolean (true if prompt needs significant changes)
- suggestions: list of specific prompt improvements
- priority: high/medium/low for the evolution
- expected_impact: description of expected improvement
"""
            
            # Validate improvement prompt
            if not SafetyValidator.is_valid_string(improvement_prompt):
                print(f"   ❌ Invalid improvement prompt")
                return self._create_default_improvements()
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": improvement_prompt}],
                temperature=0.2,
                max_tokens=1500
            )
            
            # Track API cost
            self._track_api_cost(response)
            
            improvement_text = response.choices[0].message.content
            
            # Validate improvement response
            if not SafetyValidator.validate_llm_response(improvement_text):
                print(f"   ❌ Invalid improvement response")
                return self._create_default_improvements()
            
            improvement_data = self._parse_improvement_response(improvement_text)
            
            return improvement_data
            
        except Exception as e:
            print(f"   ❌ Improvement generation failed: {e}")
            return self._create_default_improvements()
    
    def _create_default_improvements(self) -> Dict[str, Any]:
        """Create default improvements when generation fails."""
        return {
            'should_evolve': False,
            'suggestions': [],
            'priority': 'low',
            'expected_impact': 'No improvement suggestions generated'
        }
    
    def _parse_improvement_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM improvement response with safety validation."""
        try:
            if '{' in response and '}' in response:
                start = response.find('{')
                end = response.rfind('}') + 1
                if start != -1 and end != -1:
                    json_str = response[start:end]
                    data = json.loads(json_str)
                    
                    # Validate and sanitize data
                    suggestions = []
                    for suggestion in data.get('suggestions', []):
                        if isinstance(suggestion, str) and SafetyValidator.is_valid_string(suggestion):
                            suggestions.append(SafetyValidator.sanitize_string(suggestion))
                    
                    return {
                        'should_evolve': bool(data.get('should_evolve', False)),
                        'suggestions': suggestions,
                        'priority': data.get('priority', 'low'),
                        'expected_impact': SafetyValidator.sanitize_string(data.get('expected_impact', ''))
                    }
        except Exception as e:
            print(f"   ⚠️  Error parsing improvement response: {e}")
        
        return self._create_default_improvements()
    
    def _evolve_prompt(self, suggestions: List[str], evaluation: EvaluationResult):
        """Evolve the prompt based on suggestions with provenance tracking."""
        try:
            evolution_prompt = f"""
Based on the following suggestions, improve the matching prompt while maintaining its core structure and effectiveness.

SUGGESTIONS:
{chr(10).join(f"- {s}" for s in suggestions)}

CURRENT PROMPT:
{self.base_prompt}

EVALUATION CONTEXT:
Overall Score: {evaluation.overall_score}/100
Issues: {evaluation.confidence_issues + evaluation.reasoning_issues + evaluation.coverage_issues}

Provide an improved version of the prompt that addresses the suggestions while maintaining the same format and structure. Return only the improved prompt text.
"""
            
            # Validate evolution prompt
            if not SafetyValidator.is_valid_string(evolution_prompt):
                print(f"   ❌ Invalid evolution prompt")
                return
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": evolution_prompt}],
                temperature=0.3,
                max_tokens=2000
            )
            
            # Track API cost
            self._track_api_cost(response)
            
            evolved_prompt = response.choices[0].message.content.strip()
            
            # Validate evolved prompt
            if not SafetyValidator.is_valid_string(evolved_prompt):
                print(f"   ❌ Invalid evolved prompt generated")
                return
            
            # Update prompt
            self.base_prompt = evolved_prompt
            self.current_prompt_version = self._increment_version(self.current_prompt_version)
            
            # Create cost tracking snapshot
            cost_snapshot = asdict(self.cost_tracker)
            
            # Create provenance tracking
            provenance = {
                'evolution_trigger': 'performance_improvement',
                'evaluation_score': evaluation.overall_score,
                'issues_detected': len(evaluation.confidence_issues + evaluation.reasoning_issues + evaluation.coverage_issues),
                'suggestions_count': len(suggestions),
                'previous_version': self._get_previous_version(),
                'evolution_reason': 'Low performance score and specific improvement suggestions',
                'timestamp': datetime.now().isoformat()
            }
            
            # Record evolution
            evolution = PromptEvolution(
                version=self.current_prompt_version,
                timestamp=datetime.now().isoformat(),
                changes=suggestions,
                performance_metrics={
                    'overall_score': evaluation.overall_score,
                    'confidence_issues_count': len(evaluation.confidence_issues),
                    'reasoning_issues_count': len(evaluation.reasoning_issues),
                    'coverage_issues_count': len(evaluation.coverage_issues)
                },
                prompt_text=evolved_prompt,
                cost_tracking=cost_snapshot,
                provenance=provenance
            )
            
            self.prompt_history.append(evolution)
            self._save_prompt_history()
            
            print(f"   ✅ Prompt evolved to version {self.current_prompt_version}")
            print(f"   💰 Cost: ${self.cost_tracker.total_cost_usd:.4f} ({self.cost_tracker.total_tokens} tokens)")
            
        except Exception as e:
            print(f"   ❌ Prompt evolution failed: {e}")
    
    def _get_previous_version(self) -> str:
        """Get the previous prompt version."""
        if len(self.prompt_history) > 0:
            return self.prompt_history[-1].version
        return "1.0"
    
    def _increment_version(self, version: str) -> str:
        """Increment version number."""
        try:
            major, minor = version.split('.')
            return f"{major}.{int(minor) + 1}"
        except:
            return "1.1"
    
    def _save_prompt_history(self):
        """Save prompt evolution history with cost tracking."""
        try:
            history = {
                'prompts': [asdict(evolution) for evolution in self.prompt_history],
                'current_version': self.current_prompt_version,
                'last_updated': datetime.now().isoformat(),
                'total_cost_tracking': asdict(self.cost_tracker)
            }
            
            with open("adaptive_prompt_history.json", 'w') as f:
                json.dump(history, f, indent=2)
                
        except Exception as e:
            print(f"⚠️  Error saving prompt history: {e}")
    
    def _compile_adaptive_results(self, parsed_doc: ParsedDocument, matches: List[MatchResult], 
                                evaluation: EvaluationResult, improvements: Dict[str, Any]) -> Dict[str, Any]:
        """Compile comprehensive adaptive analysis results."""
        template_sections = self.template.get('sections', [])
        
        coverage = len(matches) / len(template_sections) * 100 if template_sections else 0
        
        return {
            'document_info': {
                'path': parsed_doc.filename,
                'sections_count': len(parsed_doc.sections),
                'total_content_length': len(parsed_doc.raw_text)
            },
            'matching_results': {
                'matches': [asdict(match) for match in matches],
                'coverage_percentage': coverage,
                'matches_count': len(matches),
                'template_sections_count': len(template_sections)
            },
            'evaluation': {
                'overall_score': evaluation.overall_score,
                'confidence_issues': evaluation.confidence_issues,
                'reasoning_issues': evaluation.reasoning_issues,
                'coverage_issues': evaluation.coverage_issues,
                'prompt_suggestions': evaluation.prompt_suggestions
            },
            'improvements': improvements,
            'prompt_evolution': {
                'current_version': self.current_prompt_version,
                'evolved_this_run': improvements.get('should_evolve', False),
                'total_evolutions': len(self.prompt_history)
            },
            'cost_tracking': asdict(self.cost_tracker),
            'timestamp': datetime.now().isoformat()
        }
    
    def print_adaptive_results(self, results: Dict[str, Any]):
        """Print comprehensive adaptive analysis results."""
        print("\n" + "="*80)
        print("🔄 ADAPTIVE LLM MATCHING RESULTS")
        print("="*80)
        
        # Document info
        doc_info = results['document_info']
        print(f"\n📄 DOCUMENT ANALYSIS:")
        print(f"   File: {doc_info['path']}")
        print(f"   Sections: {doc_info['sections_count']}")
        print(f"   Content Length: {doc_info['total_content_length']:,} characters")
        
        # Matching results
        matching = results['matching_results']
        print(f"\n🎯 MATCHING PERFORMANCE:")
        print(f"   Coverage: {matching['coverage_percentage']:.1f}%")
        print(f"   Matches: {matching['matches_count']}/{matching['template_sections_count']}")
        
        # Evaluation
        evaluation = results['evaluation']
        print(f"\n📊 SELF-EVALUATION:")
        print(f"   Overall Score: {evaluation['overall_score']:.1f}/100")
        
        if evaluation['confidence_issues']:
            print(f"   ⚠️  Confidence Issues: {len(evaluation['confidence_issues'])}")
        if evaluation['reasoning_issues']:
            print(f"   ⚠️  Reasoning Issues: {len(evaluation['reasoning_issues'])}")
        if evaluation['coverage_issues']:
            print(f"   ⚠️  Coverage Issues: {len(evaluation['coverage_issues'])}")
        
        # Improvements
        improvements = results['improvements']
        if improvements.get('should_evolve'):
            print(f"\n🚀 PROMPT EVOLUTION:")
            print(f"   Priority: {improvements.get('priority', 'unknown')}")
            print(f"   Expected Impact: {improvements.get('expected_impact', 'unknown')}")
            print(f"   Suggestions: {len(improvements.get('suggestions', []))}")
        
        # Prompt evolution
        evolution = results['prompt_evolution']
        print(f"\n📈 PROMPT VERSION:")
        print(f"   Current: {evolution['current_version']}")
        print(f"   Evolved This Run: {evolution['evolved_this_run']}")
        print(f"   Total Evolutions: {evolution['total_evolutions']}")
        
        # Cost tracking
        cost_tracking = results.get('cost_tracking', {})
        print(f"\n💰 COST TRACKING:")
        print(f"   Total Cost: ${cost_tracking.get('total_cost_usd', 0):.4f}")
        print(f"   Total Tokens: {cost_tracking.get('total_tokens', 0):,}")
        print(f"   API Calls: {cost_tracking.get('api_calls', 0)}")
        print(f"   Model Used: {cost_tracking.get('model_used', 'unknown')}")
        
        print("\n" + "="*80)
    
    def save_adaptive_results(self, results: Dict[str, Any], output_path: str):
        """Save adaptive analysis results."""
        try:
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"✅ Adaptive results saved to: {output_path}")
        except Exception as e:
            print(f"❌ Error saving results: {e}")


def main():
    """Main function to demonstrate adaptive LLM matching."""
    print("🚀 Adaptive LLM Matcher with Self-Evaluation")
    print("=" * 60)
    
    # Template path
    template_path = "c8500_superset_template.json"
    if not Path(template_path).exists():
        print(f"❌ Template not found: {template_path}")
        print("   Run llm_superset_template_generator.py first to create the template")
        return
    
    # Initialize adaptive matcher
    matcher = AdaptiveLLMMatcher(template_path)
    
    # Test document
    test_doc = "functional_spec.docx"
    if not Path(test_doc).exists():
        print(f"❌ Test document not found: {test_doc}")
        return
    
    # Run adaptive analysis
    results = matcher.analyze_document_adaptive(test_doc)
    
    # Print results
    matcher.print_adaptive_results(results)
    
    # Save results
    output_path = "adaptive_llm_matching_results.json"
    matcher.save_adaptive_results(results, output_path)
    
    print(f"\n🎯 Adaptive LLM matching complete!")
    print(f"   Results: {output_path}")
    print(f"   Prompt History: adaptive_prompt_history.json")


if __name__ == "__main__":
    main()
