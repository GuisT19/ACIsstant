import os
from pathlib import Path
from typing import List
from langchain_community.document_loaders import TextLoader, PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

class RAGManager:
    def __init__(self, data_dir: str = "data/uploads", index_dir: str = "data/vectordb"):
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / data_dir
        self.index_dir = self.base_dir / index_dir
        
        # CPU-friendly embedding model
        # "all-MiniLM-L6-v2" is very fast on CPU
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vector_store = None
        self.load_index()

    def load_index(self):
        if (self.index_dir / "index.faiss").exists():
            print("[RAG] Loading existing FAISS index...")
            self.vector_store = FAISS.load_local(
                str(self.index_dir), 
                self.embeddings,
                allow_dangerous_deserialization=True
            )
        else:
            print("[RAG] No index found.")

    def process_documents(self):
        print(f"[RAG] Processing documents in {self.data_dir}...")
        
        # Load Markdown
        md_loader = DirectoryLoader(str(self.data_dir), glob="**/*.md", loader_cls=TextLoader)
        # Load PDF
        pdf_loader = DirectoryLoader(str(self.data_dir), glob="**/*.pdf", loader_cls=PyPDFLoader)
        
        documents = []
        try:
            documents.extend(md_loader.load())
            documents.extend(pdf_loader.load())
        except Exception as e:
            print(f"[RAG] Error loading docs: {e}")
            
        if not documents:
            print("[RAG] No documents found to index.")
            return

        # Split
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        docs = text_splitter.split_documents(documents)
        
        # Index
        self.vector_store = FAISS.from_documents(docs, self.embeddings)
        self.vector_store.save_local(str(self.index_dir))
        print(f"[RAG] Index saved to {self.index_dir}")

    def query(self, text: str, k: int = 3) -> str:
        if not self.vector_store:
            return ""
        
        docs = self.vector_store.similarity_search(text, k=k)
        context = "\n---\n".join([doc.page_content for doc in docs])
        return context
