import os
import logging
from pathlib import Path
from typing import List
from langchain_huggingface import HuggingFaceEmbeddings # type: ignore
from langchain_text_splitters import RecursiveCharacterTextSplitter # type: ignore
from langchain_community.document_loaders import TextLoader, PyPDFLoader, DirectoryLoader # type: ignore
from langchain_community.vectorstores import FAISS # type: ignore

# Silence noisy loaders
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
logging.getLogger("pypdf").setLevel(logging.ERROR)
logging.getLogger("pypdf._reader").setLevel(logging.ERROR)

class RAGManager:
    def __init__(self, data_dir: str = "data/uploads", index_dir: str = "data/vectordb"):
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / data_dir
        self.index_dir = self.base_dir / index_dir
        
        # CPU-friendly embedding model — use local cache when available to avoid network hang
        _hf_cache = Path.home() / ".cache" / "huggingface" / "hub"
        _model_cached = (_hf_cache / "models--sentence-transformers--all-MiniLM-L6-v2").exists()
        _kwargs = {"local_files_only": True} if _model_cached else {}

        if not _model_cached:
            print("[RAG] Downloading embedding model (first run only)...")
        else:
            print("[RAG] Loading embedding model from local cache...")

        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs=_kwargs,
        )
        self.vector_store = None
        
        # Auto-scan and build on startup to ensure RAG is never empty
        if self.data_dir.exists():
            valid_files = [f for f in self.data_dir.rglob("*") if f.is_file() and f.suffix in [".pdf", ".md", ".txt"] and f.name != "README.md"]
            if valid_files:
                print(f"[RAG] Startup scan: {len(valid_files)} documents found. Synchronizing...")
                self.process_documents()
        
        self.load_index()

    def load_index(self):
        if (self.index_dir / "index.faiss").exists():
            print("[RAG] Loading existing FAISS index...")
            try:
                self.vector_store = FAISS.load_local(
                    str(self.index_dir),
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                print("[RAG] FAISS index loaded successfully.")
            except Exception as e:
                print(f"[RAG] Failed to load index ({e}). Rebuilding...")
                # Delete corrupted/incompatible index and rebuild
                import shutil
                shutil.rmtree(str(self.index_dir), ignore_errors=True)
                self.index_dir.mkdir(parents=True, exist_ok=True)
                self.vector_store = None
                if self.data_dir.exists():
                    valid_files = [f for f in self.data_dir.rglob("*")
                                   if f.is_file() and f.suffix in [".pdf", ".md", ".txt"]
                                   and f.name != "README.md"]
                    if valid_files:
                        self.process_documents()
        else:
            print("[RAG] No index found.")
            if self.data_dir.exists():
                valid_files = [f for f in self.data_dir.rglob("*") if f.is_file() and f.suffix in [".pdf", ".md", ".txt"] and f.name != "README.md"]
                if valid_files:
                    print(f"[RAG] Found {len(valid_files)} unindexed documents. Auto-indexing now...")
                    self.process_documents()

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
        self.vector_store.save_local(str(self.index_dir)) # type: ignore
        print(f"[RAG] Index saved to {self.index_dir}")

    def query(self, text: str, k: int = 3) -> str:
        if not self.vector_store:
            return ""
        
        docs = self.vector_store.similarity_search(text, k=k) # type: ignore
        context = "\n---\n".join([doc.page_content for doc in docs])
        return context
