from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

class VectorStore:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')
        self.vector_db = Chroma(embedding_function=self.embeddings)

    def add_text_to_rag(self, text, custom_id):
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        texts = text_splitter.split_text(text)

        documents = []
        for text_chunk in texts:
            doc = Document(page_content=text_chunk, metadata={'source': custom_id})
            documents.append(doc)

        self.vector_db.add_documents(documents)


    def delete_documents_by_custom_id(self, custom_id):
        self.vector_db.delete(where={'source': {'$eq': custom_id}})