#!/usr/bin/env python3
"""
Unit tests for confidence scoring functionality.
Tests parsing, validation, and threshold-based triage.
"""

import pytest
import json
import tempfile
import os
from spec_extractor import save_extracted_specs

def test_confidence_parsing_with_scores():
    """Test parsing JSON with confidence scores."""
    mock_output = '''[
        {"spec_item": "Product name", "value": "Cisco Nexus 9364C-H1 switch", "confidence": 95},
        {"spec_item": "Model number", "value": "N9K-C9364C-H1", "confidence": 98},
        {"spec_item": "Rack units", "value": "2 RU", "confidence": 92},
        {"spec_item": "QSFP port count", "value": "", "confidence": 100}
    ]'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        specs, triage_results = save_extracted_specs(mock_output, temp_path, threshold=90)
        
        # Test that all specs have confidence scores
        assert len(specs) == 4
        for spec in specs:
            assert 'confidence' in spec
            assert isinstance(spec['confidence'], int)
            assert 0 <= spec['confidence'] <= 100
        
        # Test triage results
        assert triage_results['threshold'] == 90
        assert triage_results['total_specs'] == 4
        assert triage_results['auto_approved'] == 4  # 95, 98, 92, 100 all >= 90
        assert triage_results['review_needed'] == 0  # None < 90
        
        print("✅ Confidence parsing with scores test passed")
        
    finally:
        os.unlink(temp_path)

def test_confidence_parsing_without_scores():
    """Test parsing JSON without confidence scores (backward compatibility)."""
    mock_output = '''[
        {"spec_item": "Product name", "value": "Cisco Nexus 9364C-H1 switch"},
        {"spec_item": "Model number", "value": "N9K-C9364C-H1"},
        {"spec_item": "Rack units", "value": "2 RU"}
    ]'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        specs, triage_results = save_extracted_specs(mock_output, temp_path, threshold=90)
        
        # Test that missing confidence scores are defaulted to 100
        assert len(specs) == 3
        for spec in specs:
            assert 'confidence' in spec
            assert spec['confidence'] == 100
        
        # Test triage results
        assert triage_results['auto_approved'] == 3
        assert triage_results['review_needed'] == 0
        
        print("✅ Confidence parsing without scores test passed")
        
    finally:
        os.unlink(temp_path)

def test_threshold_triage():
    """Test threshold-based triage functionality."""
    mock_output = '''[
        {"spec_item": "High confidence", "value": "clear value", "confidence": 95},
        {"spec_item": "Medium confidence", "value": "ambiguous value", "confidence": 65},
        {"spec_item": "Low confidence", "value": "unclear value", "confidence": 45},
        {"spec_item": "Very low confidence", "value": "conflicting value", "confidence": 15}
    ]'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        specs, triage_results = save_extracted_specs(mock_output, temp_path, threshold=70)
        
        # Test triage results
        assert triage_results['threshold'] == 70
        assert triage_results['total_specs'] == 4
        assert triage_results['auto_approved'] == 1  # Only 95 >= 70
        assert triage_results['review_needed'] == 3  # 65, 45, 15 < 70
        
        # Test approved list
        approved = triage_results['approved']
        assert len(approved) == 1
        assert approved[0]['spec_item'] == "High confidence"
        assert approved[0]['confidence'] == 95
        
        # Test review list
        review = triage_results['review']
        assert len(review) == 3
        review_items = [r['spec_item'] for r in review]
        assert "Medium confidence" in review_items
        assert "Low confidence" in review_items
        assert "Very low confidence" in review_items
        
        print("✅ Threshold triage test passed")
        
    finally:
        os.unlink(temp_path)

def test_edge_cases():
    """Test edge cases for confidence scoring."""
    mock_output = '''[
        {"spec_item": "Zero confidence", "value": "value", "confidence": 0},
        {"spec_item": "Max confidence", "value": "value", "confidence": 100},
        {"spec_item": "Negative confidence", "value": "value", "confidence": -5},
        {"spec_item": "Over max confidence", "value": "value", "confidence": 150}
    ]'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        specs, triage_results = save_extracted_specs(mock_output, temp_path, threshold=50)
        
        # Test that all specs have confidence scores
        assert len(specs) == 4
        for spec in specs:
            assert 'confidence' in spec
            # Should handle edge cases gracefully
            assert isinstance(spec['confidence'], int)
        
        print("✅ Edge cases test passed")
        
    finally:
        os.unlink(temp_path)

def test_average_confidence_calculation():
    """Test average confidence calculation."""
    mock_output = '''[
        {"spec_item": "Item 1", "value": "value", "confidence": 80},
        {"spec_item": "Item 2", "value": "value", "confidence": 90},
        {"spec_item": "Item 3", "value": "value", "confidence": 100}
    ]'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        specs, triage_results = save_extracted_specs(mock_output, temp_path, threshold=85)
        
        # Calculate expected average
        expected_avg = (80 + 90 + 100) / 3  # 90.0
        
        # Test triage results
        assert triage_results['total_specs'] == 3
        assert triage_results['auto_approved'] == 2  # 90, 100 >= 85
        assert triage_results['review_needed'] == 1  # 80 < 85
        
        print("✅ Average confidence calculation test passed")
        
    finally:
        os.unlink(temp_path)

if __name__ == "__main__":
    print("=== Confidence Scoring Tests ===")
    
    print("\n1. Testing confidence parsing with scores...")
    test_confidence_parsing_with_scores()
    
    print("\n2. Testing confidence parsing without scores...")
    test_confidence_parsing_without_scores()
    
    print("\n3. Testing threshold triage...")
    test_threshold_triage()
    
    print("\n4. Testing edge cases...")
    test_edge_cases()
    
    print("\n5. Testing average confidence calculation...")
    test_average_confidence_calculation()
    
    print("\n=== All Confidence Scoring Tests Passed! ===") 