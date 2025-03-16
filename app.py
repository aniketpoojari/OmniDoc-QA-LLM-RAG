from flask import Flask, render_template, request, jsonify
import uuid
import re
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from models.vector_store import VectorStore
from services.llm_service import LLMService
from services.pdf_extraction_service import extract_from_pdf
from services.website_extraction_service import extract_content_from_website

load_dotenv()

app = Flask(__name__)

# Retrieve the API key from the environment
api_key = os.getenv('GROQ_API_KEY')
vector_store = VectorStore()
llm_service = LLMService(api_key)
chat_history = []
uploads = {}

app.secret_key = 'research_assistant_secret_key'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size


@app.route('/')
def index():
    return render_template('index.html', 
                           uploads=uploads, 
                           chat_history=chat_history)

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file part'})
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No selected file'})
    
    if file and file.filename.endswith('.pdf'):
        filename = secure_filename(file.filename)

        content = extract_from_pdf(file)
        
        # Generate unique ID for document
        custom_id = str(uuid.uuid4())
        
        # Add to RAG
        vector_store.add_text_to_rag(content['text'], custom_id)
        for table in content['tables']:
            ans = llm_service.extract_info_from_table(table)
            if ans == False or ans == None:
                continue
            vector_store.add_text_to_rag(ans, custom_id)
        
        # Store in upload 
        uploads[custom_id] = {
            "name": filename,
            "type": "PDF"
        }
        
        return jsonify({
            'status': 'success', 
            'message': 'PDF uploaded and processed',
            'document': {
                'id': custom_id,
                'name': filename,
                'type': 'PDF'
            }
        })
    
    return jsonify({'status': 'error', 'message': 'Invalid file type'})

@app.route('/process_website', methods=['POST'])
def process_website():
    data = request.get_json()
    url = data.get('url')
    
    if not url:
        return jsonify({'status': 'error', 'message': 'No URL provided'})
    
    try:
        # Process website
        content = extract_content_from_website(url)
        
        # Generate unique ID for document
        custom_id = str(uuid.uuid4())
        
        # Add to RAG
        vector_store.add_text_to_rag(content['text'], custom_id)
        for table in content['tables']:
            ans = llm_service.extract_info_from_table(table)
            if ans == False or ans == None:
                continue
            vector_store.add_text_to_rag(ans, custom_id)
        
        uploads[custom_id] = {
            "name": url,
            "type": "Website"
        }

        return jsonify({
            'status': 'success', 
            'message': 'Website processed',
            'document': {
                'id': custom_id,
                'name': url,
                'type': 'Website'
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error processing website: {str(e)}'})

@app.route('/delete_document', methods=['POST'])
def delete_document():
    data = request.get_json()
    custom_id = data.get('id')
    
    if not custom_id:
        return jsonify({'status': 'error', 'message': 'No document ID provided'})
    
    if custom_id in uploads:
        # Delete document from RAG
        vector_store.delete_documents_by_custom_id(custom_id)
        
        # Remove from session
        del uploads[custom_id]
        
        return jsonify({'status': 'success', 'message': 'Document deleted'})
    
    return jsonify({'status': 'error', 'message': 'Document not found'})


def convert_to_html(text):
    # Step 1: Process bold tags
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\* (.*?)\n', r'<li>\1</li>', text)
    text = re.sub(r'\n', '<br>', text)
    return text

@app.route('/ask_question', methods=['POST'])
def ask_question():
    data = request.get_json()
    question = data.get('question')
    
    if not question:
        return jsonify({'status': 'error', 'message': 'No question provided'})
    
    # Check if there are any documents
    if not uploads:
        return jsonify({'status': 'error', 'message': 'Please upload at least one document first'})
    
    try:
        # Get AI response
        response = llm_service.ask_question(vector_store.vector_db,question)['result']
        
        # Convert to HTML
        response = convert_to_html(response)
        
        # Add messages to chat history
        chat_history.append({"role": "user", "content": question})
        chat_history.append({"role": "assistant", "content": response})
        
        return jsonify({
            'status': 'success',
            'response': response,
            'chat_history': chat_history
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error getting response: {str(e)}'})

@app.route('/clear_chat', methods=['POST'])
def clear_chat():
    global chat_history
    chat_history = []
    return jsonify({'status': 'success', 'message': 'Chat history cleared'})

if __name__ == "__main__":
    app.run(port=5000)