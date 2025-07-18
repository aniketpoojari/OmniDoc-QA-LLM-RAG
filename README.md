# 🧠 Multi-Modal RAG Question Answering System

**A comprehensive Flask-based web application that enables intelligent document analysis through RAG (Retrieval-Augmented Generation) technology. Upload PDFs or process websites to create an interactive Q&A system powered by large language models.**

## 🚀 Features

- **Multi-Format Document Support**: Process both PDF files and websites seamlessly
- **Advanced Text Extraction**: Extract text, tables, and images from documents with high accuracy
- **RAG Implementation**: Leverage ChromaDB vector storage with HuggingFace embeddings for intelligent document retrieval
- **LLM Integration**: Powered by Groq's Gemma2-9B model for natural language understanding and generation
- **Interactive Chat Interface**: Real-time Q&A with your documents through a modern Bootstrap-based UI
- **Table Processing**: Intelligent table detection and extraction with LLM-based analysis
- **Document Management**: Add, view, and delete documents with persistent storage
- **Responsive Design**: Mobile-friendly interface with smooth animations and loading states
- **Session Management**: Maintain chat history and document state across interactions

## 🔧 Quickstart

### Installation

### Environment Setup
```bash
# Add your Groq API key
echo "GROQ_API_KEY=your_groq_api_key_here" >> .env
```

### Required Dependencies
```bash
pip install -r requirements.txt
```

### Running the Application
```bash
# Start the Flask development server
python app.py

# Access the application
# Open your browser and navigate to: http://localhost:5000
```

### Usage Instructions
1. **Upload Documents**: Choose between PDF upload or website processing
2. **Document Processing**: The system automatically extracts text, tables, and metadata
3. **Ask Questions**: Use the chat interface to query your documents intelligently
4. **Manage Documents**: View uploaded documents and delete them as needed
5. **Chat History**: Access previous conversations and clear history when needed

## 📌 Results

### Core Functionality
- **Document Processing**: Successfully extracts and processes text from PDFs and websites
- **Vector Storage**: Implements efficient document chunking and embedding storage
- **Question Answering**: Provides contextually relevant answers based on document content
- **Table Analysis**: Intelligently processes and extracts structured data from tables
- **Real-time Interface**: Responsive chat interface with loading states and error handling

### Technical Architecture
- **Backend**: Flask web framework with modular service architecture
- **Vector Database**: ChromaDB for efficient similarity search
- **Embeddings**: HuggingFace sentence-transformers for document representation
- **LLM**: Groq API integration with Gemma2-9B model
- **Frontend**: Bootstrap 5 with custom CSS and jQuery for interactivity