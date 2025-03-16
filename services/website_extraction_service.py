from PIL import Image
from io import BytesIO
import base64
import requests
from bs4 import BeautifulSoup
import pandas as pd


def extract_content_from_website(url):
    # Fetch webpage content
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract text (all text in the body)
    text = soup.get_text()

    # Extract tables and convert them to pandas DataFrame
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
            df = pd.DataFrame(table_data, columns=headers)
            tables.append(df)

    # Extract images and encode them in base64
    images = []
    for img_tag in soup.find_all('img'):
        img_url = img_tag.get('src')
        if img_url:
            # Handle relative image URLs by converting them to absolute URLs
            if not img_url.startswith('http'):
                img_url = requests.compat.urljoin(url, img_url)
            try:
                img_response = requests.get(img_url)
                img = Image.open(BytesIO(img_response.content))
                img_format = img.format  # JPEG, PNG, etc.
                
                # Convert image to base64
                img_buffer = BytesIO()
                img.save(img_buffer, format=img_format)
                encoded_image = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
                
                # Store image data in metadata
                images.append({
                    'url': img_url,
                    'base64': encoded_image,
                    'format': img_format,
                    'width': img.width,
                    'height': img.height
                })
            except Exception as e:
                pass

    return {
        'text': text,
        'tables': tables,
        'images': images
    }