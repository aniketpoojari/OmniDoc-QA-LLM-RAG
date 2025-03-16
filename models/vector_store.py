from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

class VectorStore:
    def __init__(self):

        # Initialize embedding model and ChromaDB
        self.embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')
        self.vector_db = Chroma(embedding_function=self.embeddings)

    # Function to add text to RAG
    def add_text_to_rag(self, text, custom_id):
        # Initialize the text splitter
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        
        # Split the text into chunks
        texts = text_splitter.split_text(text)
        
        # Create Document objects with the provided custom ID
        documents = []
        for text_chunk in texts:
            doc = Document(page_content=text_chunk, metadata={'source': custom_id})
            documents.append(doc)
        
        # Add documents to ChromaDB with the custom ID
        self.vector_db.add_documents(documents)


    def delete_documents_by_custom_id(self, custom_id):
        self.vector_db.delete(where={'source': {'$eq': custom_id}})