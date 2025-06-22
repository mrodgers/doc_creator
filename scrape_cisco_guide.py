#!/usr/bin/env python3
"""
Scrape Cisco Catalyst 9300 Series Switches Hardware Installation Guide

- Fetches the Table of Contents (ToC) page
- Extracts all section links
- Downloads and parses each section's HTML
- Saves each section as a structured JSON file

Usage:
    uv run scrape_cisco_guide.py --toc_url <ToC URL> --output_dir <output_dir>

Default ToC URL:
    https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst9300/hardware/install/b_c9300_hig.html
"""

import requests
from bs4 import BeautifulSoup
import os
import json
import argparse
import time
from urllib.parse import urljoin, urlparse

DEFAULT_TOC_URL = "https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst9300/hardware/install/b_c9300_hig.html"
BASE_URL = "https://www.cisco.com"


def get_section_links(toc_url):
    resp = requests.get(toc_url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    links = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        # Only keep links to HTML sections in the same guide
        if href.endswith('.html') and 'b_c9300_hig' in href:
            full_url = urljoin(BASE_URL, href)
            if full_url not in links:
                links.append(full_url)
    return links


def scrape_section(url):
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    # Extract main content (try to find main/article/section, fallback to body)
    main = soup.find('main') or soup.find('article') or soup.find('section') or soup.body
    if not main:
        return None
    # Extract title
    title = soup.title.string.strip() if soup.title else url
    # Extract all headings and paragraphs
    content_blocks = []
    for tag in main.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'table']):
        block = {
            'tag': tag.name,
            'text': tag.get_text(separator=' ', strip=True)
        }
        if tag.name in ['ul', 'ol']:
            block['items'] = [li.get_text(strip=True) for li in tag.find_all('li')]
        if tag.name == 'table':
            rows = []
            for tr in tag.find_all('tr'):
                cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                rows.append(cells)
            block['rows'] = rows
        content_blocks.append(block)
    # Extract all links (with text and resolved URLs)
    links = []
    for a in main.find_all('a', href=True):
        link_url = urljoin(url, a['href'])
        link_text = a.get_text(strip=True)
        links.append({'text': link_text, 'url': link_url})
    return {
        'url': url,
        'title': title,
        'content_blocks': content_blocks,
        'links': links
    }


def main():
    parser = argparse.ArgumentParser(description="Scrape Cisco Catalyst 9300 Hardware Installation Guide")
    parser.add_argument('--toc_url', default=DEFAULT_TOC_URL, help='URL of the Table of Contents page')
    parser.add_argument('--output_dir', default='scraped_cisco_guide', help='Directory to save scraped sections')
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    print(f"Fetching Table of Contents: {args.toc_url}")
    section_links = get_section_links(args.toc_url)
    print(f"Found {len(section_links)} section links.")

    for i, link in enumerate(section_links, 1):
        print(f"[{i}/{len(section_links)}] Scraping: {link}")
        try:
            section_data = scrape_section(link)
            if section_data:
                # Use the last part of the URL as filename
                parsed = urlparse(link)
                filename = os.path.basename(parsed.path).replace('.html', '.json')
                out_path = os.path.join(args.output_dir, filename)
                with open(out_path, 'w', encoding='utf-8') as f:
                    json.dump(section_data, f, indent=2, ensure_ascii=False)
                print(f"  Saved to {out_path}")
            else:
                print(f"  Warning: No main content found for {link}")
        except Exception as e:
            print(f"  Error scraping {link}: {e}")
        time.sleep(1)  # Be polite to Cisco's servers

    print(f"\nScraping complete. All sections saved to: {args.output_dir}")

if __name__ == "__main__":
    main() 