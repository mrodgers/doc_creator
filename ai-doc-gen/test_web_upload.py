#!/usr/bin/env python3
"""
Test script for web upload functionality.
"""

import os
import time
import requests
from pathlib import Path

# Get the web UI port from environment variable
WEB_PORT = os.getenv('WEB_PORT', '5476')
BASE_URL = f'http://localhost:{WEB_PORT}'

def test_web_upload():
    """Test the web upload functionality."""
    print("🧪 Testing Web Upload Functionality")
    print("=" * 50)
    
    # Test 1: Check if the web UI is running
    print("1. Checking if web UI is running...")
    try:
        response = requests.get(f'{BASE_URL}/')
        if response.status_code == 200:
            print("✅ Web UI is running")
        else:
            print(f"❌ Web UI returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Web UI is not running")
        print(f"💡 Start it with: cd ai-doc-gen && podman-compose up -d")
        return False
    
    # Test 2: Upload a test PDF
    print("\n2. Testing PDF upload...")
    test_pdf = Path("examples/cisco_nexus_9000_series.pdf")
    
    if not test_pdf.exists():
        print(f"❌ Test PDF not found: {test_pdf}")
        return False
    
    try:
        with open(test_pdf, 'rb') as f:
            files = {'file': (test_pdf.name, f, 'application/pdf')}
            response = requests.post(f'{BASE_URL}/upload', files=files)
        
        if response.status_code == 200:
            result = response.json()
            job_id = result.get('job_id')
            print(f"✅ Upload successful, job ID: {job_id}")
        else:
            print(f"❌ Upload failed with status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return False
    
    # Test 3: Check processing results
    print("\n3. Checking processing results...")
    max_wait = 60  # Wait up to 60 seconds
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            results_response = requests.get(f'{BASE_URL}/results/{job_id}')
            if results_response.status_code == 200:
                results = results_response.json()
                status = results.get('status')
                
                if status == 'completed':
                    print("✅ Processing completed successfully")
                    print(f"📊 Confidence: {results.get('confidence', 'N/A')}")
                    return True
                elif status == 'failed':
                    print(f"❌ Processing failed: {results.get('error', 'Unknown error')}")
                    return False
                else:
                    print(f"⏳ Processing status: {status}")
                    time.sleep(2)
            else:
                print(f"❌ Failed to get results: {results_response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error checking results: {e}")
            return False
    
    print("❌ Processing timed out")
    return False

if __name__ == "__main__":
    success = test_web_upload()
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n❌ Tests failed!")
        exit(1)
