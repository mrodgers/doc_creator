#!/usr/bin/env python3
"""
Test script for enhanced HTML parser with improved scraping methods.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ai_doc_gen.input_processing.document_parser import HTMLParser, DocumentParserFactory
import json

def test_enhanced_html_parser():
    """Test the enhanced HTML parser with the Cisco webpage."""
    
    # Check if the webpage.html file exists
    html_file = "webpage.html"
    if not os.path.exists(html_file):
        print(f"❌ HTML file {html_file} not found")
        return False
    
    print("🧪 Testing Enhanced HTML Parser")
    print("=" * 50)
    
    try:
        # Create parser factory
        factory = DocumentParserFactory()
        
        # Get HTML parser
        parser = factory.get_parser(html_file)
        if not parser:
            print("❌ Could not get HTML parser")
            return False
        
        print(f"✅ HTML parser created: {type(parser).__name__}")
        
        # Parse the document
        print(f"📄 Parsing {html_file}...")
        parsed_doc = parser.parse(html_file)
        
        print(f"✅ Document parsed successfully")
        print(f"   - Title: {parsed_doc.title}")
        print(f"   - File type: {parsed_doc.file_type}")
        print(f"   - Sections found: {len(parsed_doc.sections)}")
        print(f"   - Raw text length: {len(parsed_doc.raw_text)} characters")
        print(f"   - Parsing errors: {len(parsed_doc.parsing_errors)}")
        
        if parsed_doc.parsing_errors:
            print("⚠️  Parsing errors:")
            for error in parsed_doc.parsing_errors:
                print(f"   - {error}")
        
        # Show first few sections
        print("\n📋 First 5 sections:")
        for i, section in enumerate(parsed_doc.sections[:5]):
            print(f"   {i+1}. {section['heading']} (Level {section['level']})")
            print(f"      Content items: {len(section['content'])}")
            if section['content']:
                print(f"      First content: {section['content'][0][:100]}...")
            print()
        
        # Check for table content
        table_sections = [s for s in parsed_doc.sections if any('Table' in str(c) for c in s['content'])]
        print(f"📊 Sections with tables: {len(table_sections)}")
        
        # Save results for comparison
        output_file = "enhanced_html_parser_results.json"
        with open(output_file, 'w') as f:
            # Convert to dict for JSON serialization
            doc_dict = parsed_doc.model_dump()
            json.dump(doc_dict, f, indent=2, default=str)
        
        print(f"💾 Results saved to {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing enhanced HTML parser: {e}")
        import traceback
        traceback.print_exc()
        return False

def compare_with_original():
    """Compare enhanced parser results with original scraper results."""
    
    print("\n🔄 Comparing with Original Scraper Results")
    print("=" * 50)
    
    # Check if we have original scraper results
    original_dir = "scraped_cisco_guide"
    if not os.path.exists(original_dir):
        print(f"❌ Original scraper results directory {original_dir} not found")
        return
    
    # Count original files
    original_files = [f for f in os.listdir(original_dir) if f.endswith('.json')]
    print(f"📁 Original scraper files: {len(original_files)}")
    
    # Check enhanced parser results
    enhanced_file = "enhanced_html_parser_results.json"
    if os.path.exists(enhanced_file):
        with open(enhanced_file, 'r') as f:
            enhanced_data = json.load(f)
        
        print(f"📊 Enhanced parser sections: {len(enhanced_data['sections'])}")
        print(f"📝 Enhanced parser content items: {sum(len(s['content']) for s in enhanced_data['sections'])}")
        
        # Show section headings from enhanced parser
        print("\n📋 Enhanced parser section headings:")
        for i, section in enumerate(enhanced_data['sections'][:10]):
            print(f"   {i+1}. {section['heading']}")
        
        if len(enhanced_data['sections']) > 10:
            print(f"   ... and {len(enhanced_data['sections']) - 10} more sections")

if __name__ == "__main__":
    success = test_enhanced_html_parser()
    
    if success:
        compare_with_original()
        print("\n✅ Enhanced HTML parser test completed successfully!")
    else:
        print("\n❌ Enhanced HTML parser test failed!")
        sys.exit(1) 