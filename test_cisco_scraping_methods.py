import requests
from bs4 import BeautifulSoup
import pandas as pd
import trafilatura

URL = 'https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst9300/hardware/install/b_c9300_hig/Configuring-a-switch.html'

print(f"Fetching: {URL}")
resp = requests.get(URL)
resp.raise_for_status()
html = resp.text

print("\n=== BeautifulSoup: Headings and Paragraphs ===")
soup = BeautifulSoup(html, 'html.parser')
for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
    print(f"[{tag.name}] {tag.get_text(strip=True)}")
for p in soup.find_all('p'):
    print(f"[p] {p.get_text(strip=True)}")

print("\n=== BeautifulSoup: Notes/Warnings (by image alt or table) ===")
for img in soup.find_all('img', alt=True):
    if 'note' in img['alt'].lower() or 'warning' in img['alt'].lower():
        parent = img.find_parent('table')
        if parent:
            print('NOTE/WARNING:', parent.get_text(separator=' ', strip=True))

print("\n=== BeautifulSoup: Tables (first 2 rows of each) ===")
for i, table in enumerate(soup.find_all('table'), 1):
    print(f"Table {i}:")
    for j, row in enumerate(table.find_all('tr')):
        if j >= 2:
            break
        cells = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
        print('  ', cells)

print("\n=== pandas.read_html: All Tables (first 2 rows of each) ===")
tables = pd.read_html(html)
for i, df in enumerate(tables, 1):
    print(f"pandas Table {i} (shape {df.shape}):")
    print(df.head(2))

print("\n=== trafilatura: Main Content Extraction ===")
main_content = trafilatura.extract(html)
print(main_content[:1000] + '...') 