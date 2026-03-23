import os
from pathlib import Path
from typing import List
from langchain_community.document_loaders import TextLoader, PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from .config import UPLOADS_DIR, INDEX_DIR

class RAGManager:
    def __init__(self):
        self.data_dir = UPLOADS_DIR
        self.index_dir = INDEX_DIR
        
        # CPU-friendly embedding model
        # "all-MiniLM-L6-v2" is very fast on CPU
        try:
            self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        except Exception as e:
            print(f"[RAG] Error loading embeddings: {e}")
            self.embeddings = None
            
        self.vector_store = None
        self.load_index()

    def load_index(self):
        if self.embeddings and (self.index_dir / "index.faiss").exists():
            print("[RAG] Loading existing FAISS index...")
            try:
                self.vector_store = FAISS.load_local(
                    str(self.index_dir), 
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
            except Exception as e:
                print(f"[RAG] Error loading local index: {e}")
        else:
            print("[RAG] No vector index found.")

    def process_documents(self):
        print(f"[RAG] Processing documents in {self.data_dir}...")
        
        # Create loader for MD and PDF
        md_loader = DirectoryLoader(str(self.data_dir), glob="**/*.md", loader_cls=TextLoader)
        pdf_loader = DirectoryLoader(str(self.data_dir), glob="**/*.pdf", loader_cls=PyPDFLoader)
        
        documents = []
        try:
            documents.extend(md_loader.load())
            documents.extend(pdf_loader.load())
        except Exception as e:
            print(f"[RAG] Warning during doc load: {e}")
            
        if not documents:
            print("[RAG] No documents found to index.")
            return

        # Split text
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        docs = text_splitter.split_documents(documents)
        
        # Build index
        if self.embeddings:
            self.vector_store = FAISS.from_documents(docs, self.embeddings)
            assert self.vector_store is not None
            self.vector_store.save_local(str(self.index_dir))
            print(f"[RAG] Index successfully saved to {self.index_dir}")
        else:
            print("[RAG] Error: Embeddings not available.")

    def query(self, text: str, k: int = 3) -> str:
        if not self.vector_store:
            return ""
        
        assert self.vector_store is not None
        docs = self.vector_store.similarity_search(text, k=k)
        context = "\n---\n".join([doc.page_content for doc in docs])
        return context
