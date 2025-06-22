#!/usr/bin/env python3
"""
Test web UI upload functionality with serialization fix.
"""

import requests
import json
from pathlib import Path

def test_web_upload():
    """Test the web UI upload endpoint."""
    print("Testing web UI upload...")
    
    # Check if the server is running
    try:
        response = requests.get('http://localhost:5432/')
        if response.status_code == 200:
            print("✅ Web UI is running")
        else:
            print(f"❌ Web UI returned status {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Web UI is not running. Please start it with: uv run python launch_ui.py")
        return
    
    # Test with a simple text file
    test_file_path = Path("test_upload.txt")
    test_content = "This is a test document for upload testing."
    
    # Create test file
    with open(test_file_path, 'w') as f:
        f.write(test_content)
    
    try:
        # Test upload
        with open(test_file_path, 'rb') as f:
            files = {'document': f}
            response = requests.post('http://localhost:5432/upload', files=files)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Upload successful!")
            print(f"Job ID: {result.get('job_id')}")
            print(f"Status: {result.get('status')}")
            print(f"Filename: {result.get('filename')}")
            
            # Test getting results
            job_id = result.get('job_id')
            if job_id:
                results_response = requests.get(f'http://localhost:5432/results/{job_id}')
                if results_response.status_code == 200:
                    print("✅ Results retrieval successful!")
                else:
                    print(f"❌ Results retrieval failed: {results_response.status_code}")
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    finally:
        # Clean up test file
        if test_file_path.exists():
            test_file_path.unlink()

if __name__ == "__main__":
    test_web_upload() 