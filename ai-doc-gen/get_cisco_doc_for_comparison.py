#!/usr/bin/env python3
"""
Download Cisco Catalyst 9300 documentation for 1:1 comparison.
"""

import requests
from pathlib import Path
import time


def download_cisco_doc():
    """Download the main Cisco Catalyst 9300 documentation page."""
    
    # Cisco Catalyst 9300 Hardware Installation Guide URL - try chapter 1
    url = "https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst9300/hardware/install/b_9300_hig/b_9300_hig_chapter_01.html"
    
    print(f"🌐 Downloading Cisco documentation from: {url}")
    
    try:
        # Add headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Save the HTML content
        output_file = "cisco_doc_comparison.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        print(f"✅ Downloaded {len(response.text)} characters to {output_file}")
        print(f"📄 File size: {Path(output_file).stat().st_size / 1024:.1f} KB")
        
        return output_file
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error downloading document: {e}")
        return None


def get_alternative_urls():
    """Get alternative URLs for Cisco documentation."""
    urls = [
        "https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst9300/hardware/install/b_9300_hig/b_9300_hig_chapter_01.html",
        "https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst9300/hardware/install/b_9300_hig/b_9300_hig_chapter_02.html",
        "https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst9300/hardware/install/b_9300_hig/b_9300_hig_chapter_03.html"
    ]
    
    print("\n📚 Alternative Cisco documentation URLs:")
    for i, url in enumerate(urls, 1):
        print(f"   {i}. {url}")
    
    return urls


def main():
    """Main function to download Cisco documentation."""
    print("🔍 Cisco Catalyst 9300 Documentation Downloader")
    print("=" * 50)
    
    # Download main page
    downloaded_file = download_cisco_doc()
    
    if downloaded_file:
        print(f"\n✅ Success! You can now use '{downloaded_file}' for 1:1 comparison")
        print(f"   Run: python model_comparison_1to1.py")
    else:
        print("\n❌ Download failed. Here are alternative options:")
        get_alternative_urls()
        print("\n💡 You can manually download from the URLs above or use the existing webpage.html")


if __name__ == "__main__":
    main() 