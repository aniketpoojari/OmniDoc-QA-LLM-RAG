from flask import Flask, render_template, request, jsonify
import uuid
import re
import os
import time
from dotenv import load_dotenv, dotenv_values
from werkzeug.utils import secure_filename
from models.vector_store import VectorStore
from services.llm_service import LLMService
from services.pdf_extraction_service import extract_from_pdf
from services.website_extraction_service import extract_content_from_website
from services.monitoring_service import log_request, record_feedback

load_dotenv(override=True)

# Retrieve the API key — prioritize .env file over system env vars
_dotenv_vars = dotenv_values('.env')
api_key = _dotenv_vars.get('GROQ_API_KEY') or os.getenv('GROQ_API_KEY')
if not api_key:
    print("CRITICAL: GROQ_API_KEY not found in .env or environment variables!")
else:
    source = ".env file" if 'GROQ_API_KEY' in _dotenv_vars else "system env"
    print(f"DEBUG: GROQ_API_KEY loaded from {source}, starting with: {api_key[:5]}...")

app = Flask(__name__)
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

@app.route('/feedback', methods=['POST'])
def feedback():
    data = request.get_json()
    is_relevant = data.get('relevant')
    if is_relevant is not None:
        record_feedback(is_relevant)
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Missing feedback field'}), 400

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
        content = extract_content_from_website(url)

        custom_id = str(uuid.uuid4())

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
    start_time = time.time()
    data = request.get_json()
    question = data.get('question')
    
    if not question:
        return jsonify({'status': 'error', 'message': 'No question provided'})

    if not uploads:
        return jsonify({'status': 'error', 'message': 'Please upload at least one document first'})
    
    try:
        # Get AI response
        res = llm_service.ask_question(vector_store.vector_db, question)
        response_text = res['result']
        
        # Convert to HTML
        response_html = convert_to_html(response_text)
        
        # Add messages to chat history
        chat_history.append({"role": "user", "content": question})
        chat_history.append({"role": "assistant", "content": response_html})
        
        latency = time.time() - start_time

        # Log the request
        log_request(
            query=question,
            latency=latency,
            tokens_input=res['tokens_input'],
            tokens_output=res['tokens_output'],
            chunks_retrieved=res['chunks_count']
        )
        
        return jsonify({
            'status': 'success',
            'response': response_html,
            'chat_history': chat_history,
            'metrics': {
                'latency': round(latency, 2),
                'chunks_count': res['chunks_count'],
                'tokens_input': res['tokens_input'],
                'tokens_output': res['tokens_output']
            }
        })
    except Exception as e:
        log_request(
            query=question,
            latency=time.time() - start_time,
            tokens_input=0,
            tokens_output=0,
            chunks_retrieved=0,
            error=e
        )
        return jsonify({'status': 'error', 'message': f'Error getting response: {str(e)}'})

@app.route('/clear_chat', methods=['POST'])
def clear_chat():
    global chat_history
    chat_history = []
    return jsonify({'status': 'success', 'message': 'Chat history cleared'})

if __name__ == "__main__":
    port = int(os.getenv('PORT', 7860))
    app.run(host="0.0.0.0", port=port)