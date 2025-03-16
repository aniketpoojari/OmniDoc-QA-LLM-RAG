import fitz
import tabula
from io import BytesIO
import base64
from PIL import Image

def extract_from_pdf(pdf_file):

    # Open the PDF file
    doc = doc = fitz.open(stream=BytesIO(pdf_file.read()))
    
    # Extract text from each page
    text = ""
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text += page.get_text() + "\n"

    # Reset the file pointer to the beginning
    pdf_file.seek(0)

    # Extract tables from the PDF file
    tables = tabula.read_pdf(pdf_file, pages="all", multiple_tables=True, encoding='ISO-8859-1')
    
    # Extract images from the PDF
    extracted_images = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        image_list = page.get_images(full=True)

        for image_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]

            # Convert image to JPEG
            img_pil = Image.open(BytesIO(image_bytes))
            img_pil = img_pil.convert("RGB")  # Ensure compatibility for JPEG
            img_buffer = BytesIO()
            img_pil.save(img_buffer, format="JPEG")

            # Encode image bytes as base64
            encoded_image = base64.b64encode(img_buffer.getvalue()).decode('utf-8')

            # Store image in list with metadata
            extracted_images.append({
                "page": page_num + 1,
                "index": image_index + 1,
                "format": "jpeg",  # JPEG format
                "image_base64": encoded_image,  # Base64-encoded image
                "width": img_pil.width,
                "height": img_pil.height
            })

    return {
        'text': text,
        'tables': tables,
        'images': extracted_images
    }