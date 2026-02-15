import re
import requests
from bs4 import BeautifulSoup, Comment
from urllib.parse import urljoin
import pandas as pd


def extract_content_from_website(url):
    # Fetch webpage with browser-like headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
    response.raise_for_status()

    # Handle encoding - requests sometimes guesses wrong
    if response.encoding and response.encoding.lower() != 'utf-8':
        response.encoding = response.apparent_encoding

    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract tables BEFORE removing elements (so we don't lose tables in removed sections)
    tables = _extract_tables(soup)

    # Extract clean text
    text = _extract_text(soup)

    if not text or len(text.strip()) < 50:
        raise ValueError(f"Could not extract meaningful content from {url}. The page may require JavaScript or may be blocking automated access.")

    return {
        'text': text,
        'tables': tables,
        'images': []
    }


def _extract_text(soup):
    # Work on a copy so we don't mutate the original
    soup = BeautifulSoup(str(soup), 'html.parser')

    # Remove non-content elements
    tags_to_remove = [
        'script', 'style', 'noscript', 'iframe', 'svg',
        'nav', 'footer', 'header',
        'aside', 'form', 'button',
    ]
    for tag in soup.find_all(tags_to_remove):
        tag.decompose()

    # Remove HTML comments
    for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
        comment.extract()

    # Remove hidden elements
    for tag in soup.find_all(attrs={'style': re.compile(r'display\s*:\s*none', re.I)}):
        tag.decompose()
    for tag in soup.find_all(attrs={'hidden': True}):
        tag.decompose()
    for tag in soup.find_all(attrs={'aria-hidden': 'true'}):
        tag.decompose()

    # Try to find the main content area first
    main_content = (
        soup.find('main') or
        soup.find('article') or
        soup.find('div', role='main') or
        soup.find('div', id=re.compile(r'content|main|article|post|entry', re.I)) or
        soup.find('div', class_=re.compile(r'content|main|article|post|entry', re.I))
    )

    source = main_content if main_content else soup.find('body') or soup

    # Extract text with newline separators
    raw_text = source.get_text(separator='\n', strip=True)

    # Clean up the text
    lines = raw_text.splitlines()
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        # Skip very short lines (likely menu items, icons, etc.)
        if len(line) < 3:
            continue
        cleaned_lines.append(line)

    text = '\n'.join(cleaned_lines)

    # Collapse multiple blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def _extract_tables(soup):
    tables = []
    for table in soup.find_all('table'):
        table_data = []
        headers = [header.get_text(strip=True) for header in table.find_all('th')]
        rows = table.find_all('tr')

        for row in rows:
            cells = row.find_all('td')
            row_data = [cell.get_text(strip=True) for cell in cells]
            if row_data:
                table_data.append(row_data)

        if table_data:
            if headers and len(headers) == len(table_data[0]):
                df = pd.DataFrame(table_data, columns=headers)
            else:
                df = pd.DataFrame(table_data)
            tables.append(df.to_string(index=False))

    return tables
