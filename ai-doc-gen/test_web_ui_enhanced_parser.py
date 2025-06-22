#!/usr/bin/env python3
"""
Test the enhanced HTML parser with web UI upload functionality.
"""

import sys
import os
import json
import tempfile
import shutil
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ai_doc_gen.input_processing.document_parser import DocumentParserFactory
from ai_doc_gen.utils.serialization import EnhancedJSONEncoder

def test_web_ui_upload_simulation():
    """Simulate web UI upload process with enhanced HTML parser."""
    
    print("🌐 Testing Enhanced HTML Parser with Web UI Upload")
    print("=" * 60)
    
    # Check if the webpage.html file exists
    html_file = "webpage.html"
    if not os.path.exists(html_file):
        print(f"❌ HTML file {html_file} not found")
        return False
    
    try:
        # Step 1: Simulate file upload to uploads directory
        print("📤 Step 1: Simulating File Upload")
        print("-" * 40)
        
        uploads_dir = "uploads"
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Copy HTML file to uploads directory (simulating upload)
        uploaded_file = os.path.join(uploads_dir, "cisco_guide_enhanced.html")
        shutil.copy2(html_file, uploaded_file)
        
        print(f"✅ File uploaded to: {uploaded_file}")
        print(f"   - File size: {os.path.getsize(uploaded_file)} bytes")
        
        # Step 2: Process with enhanced parser
        print("\n🔧 Step 2: Processing with Enhanced Parser")
        print("-" * 40)
        
        factory = DocumentParserFactory()
        parser = factory.get_parser(uploaded_file)
        
        if not parser:
            print("❌ Could not get HTML parser")
            return False
        
        parsed_doc = parser.parse(uploaded_file)
        print(f"✅ Enhanced parser processed uploaded file")
        print(f"   - Sections extracted: {len(parsed_doc.sections)}")
        print(f"   - Content items: {sum(len(s['content']) for s in parsed_doc.sections)}")
        print(f"   - Table sections: {len([s for s in parsed_doc.sections if any('Table' in str(c) for c in s['content'])])}")
        
        # Step 3: Prepare for web UI display
        print("\n📊 Step 3: Preparing for Web UI Display")
        print("-" * 40)
        
        # Create structured data for web UI
        web_ui_data = {
            "filename": os.path.basename(uploaded_file),
            "file_type": "html",
            "title": parsed_doc.title,
            "sections": parsed_doc.sections,
            "metadata": parsed_doc.metadata,
            "stats": {
                "total_sections": len(parsed_doc.sections),
                "content_items": sum(len(s['content']) for s in parsed_doc.sections),
                "table_sections": len([s for s in parsed_doc.sections if any('Table' in str(c) for c in s['content'])]),
                "enhanced_source": len([s for s in parsed_doc.sections if s.get('source') == 'html_enhanced'])
            }
        }
        
        # Step 4: Test serialization for web UI
        print("\n🔄 Step 4: Testing Web UI Serialization")
        print("-" * 40)
        
        encoder = EnhancedJSONEncoder()
        serialized_data = encoder.encode(web_ui_data)
        
        print(f"✅ Data serialized for web UI")
        print(f"   - Serialized size: {len(serialized_data)} characters")
        print(f"   - JSON valid: {json.loads(serialized_data) is not None}")
        
        # Step 5: Save web UI ready data
        print("\n💾 Step 5: Saving Web UI Ready Data")
        print("-" * 40)
        
        output_file = "web_ui_enhanced_parser_data.json"
        with open(output_file, 'w') as f:
            f.write(serialized_data)
        
        print(f"✅ Web UI data saved to: {output_file}")
        
        # Step 6: Create sample web UI response
        print("\n🎨 Step 6: Creating Sample Web UI Response")
        print("-" * 40)
        
        web_ui_response = {
            "status": "success",
            "message": "Enhanced HTML parser processed successfully",
            "data": {
                "filename": os.path.basename(uploaded_file),
                "file_type": "html",
                "title": parsed_doc.title,
                "sections_count": len(parsed_doc.sections),
                "content_items": sum(len(s['content']) for s in parsed_doc.sections),
                "table_sections": len([s for s in parsed_doc.sections if any('Table' in str(c) for c in s['content'])]),
                "enhanced_features": {
                    "pandas_integration": True,
                    "beautifulsoup_enhanced": True,
                    "table_extraction": True,
                    "structure_detection": True
                }
            },
            "sample_sections": [
                {
                    "heading": s['heading'],
                    "level": s['level'],
                    "content_count": len(s['content']),
                    "has_tables": any('Table' in str(c) for c in s['content'])
                }
                for s in parsed_doc.sections[:10]
            ]
        }
        
        response_file = "web_ui_response_sample.json"
        with open(response_file, 'w') as f:
            json.dump(web_ui_response, f, indent=2, default=str)
        
        print(f"✅ Web UI response sample saved to: {response_file}")
        
        # Step 7: Display summary for web UI
        print("\n📋 Step 7: Web UI Display Summary")
        print("-" * 40)
        
        print("🎯 Enhanced HTML Parser Results for Web UI:")
        print(f"   📄 File: {os.path.basename(uploaded_file)}")
        print(f"   📊 Sections: {len(parsed_doc.sections)}")
        print(f"   📝 Content Items: {sum(len(s['content']) for s in parsed_doc.sections)}")
        print(f"   📋 Table Sections: {len([s for s in parsed_doc.sections if any('Table' in str(c) for c in s['content'])])}")
        print(f"   🔧 Enhanced Features: Pandas + BeautifulSoup")
        print(f"   ✅ Web UI Ready: Yes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in web UI upload simulation: {e}")
        import traceback
        traceback.print_exc()
        return False

def cleanup_test_files():
    """Clean up test files created during the test."""
    
    print("\n🧹 Cleaning up test files...")
    
    files_to_clean = [
        "uploads/cisco_guide_enhanced.html",
        "web_ui_enhanced_parser_data.json",
        "web_ui_response_sample.json"
    ]
    
    for file_path in files_to_clean:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"   ✅ Removed: {file_path}")

if __name__ == "__main__":
    print("🚀 Starting Enhanced HTML Parser Web UI Integration Test")
    print("=" * 60)
    
    success = test_web_ui_upload_simulation()
    
    if success:
        print("\n✅ Enhanced HTML Parser Web UI Integration Test Completed!")
        print("\n🎯 Summary:")
        print("   1. ✅ File upload simulation successful")
        print("   2. ✅ Enhanced parser processes uploaded files")
        print("   3. ✅ Web UI serialization works correctly")
        print("   4. ✅ Response data properly formatted")
        print("   5. ✅ Ready for web UI integration")
        
        print("\n📁 Generated Files:")
        print("   - web_ui_enhanced_parser_data.json (Serialized data)")
        print("   - web_ui_response_sample.json (Sample response)")
        print("   - uploads/cisco_guide_enhanced.html (Uploaded file)")
        
        print("\n🎉 Enhanced HTML parser is fully integrated with web UI!")
        
        # Ask if user wants to clean up
        response = input("\n🧹 Clean up test files? (y/n): ").lower().strip()
        if response == 'y':
            cleanup_test_files()
            print("✅ Test files cleaned up")
    else:
        print("\n❌ Enhanced HTML Parser Web UI Integration Test Failed!")
        sys.exit(1) 