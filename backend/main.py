import warnings
import os
import threading
import msvcrt
import signal
from pathlib import Path
from contextlib import asynccontextmanager

# Suppress noisy third-party warnings before any imports
warnings.filterwarnings("ignore")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")

import uuid
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request # type: ignore
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from fastapi.staticfiles import StaticFiles # type: ignore
from pydantic import BaseModel # type: ignore
from typing import List, Optional, Dict
import threading
import msvcrt
import signal

from backend.llm import LLMManager
from backend.database import ChatDB
from backend.rag import RAGManager

# --- API initialization ---
def terminal_watcher():
    """Listens for Ctrl+R in the terminal window to restart the AI."""
    while True:
        if msvcrt.kbhit(): # type: ignore
            ch = msvcrt.getch() # type: ignore
            # Ctrl+R is character 18 (0x12) in binary mode on Windows
            if ch == b'\x12' or ch == b'\x12\r':
                print("\n  [!!] HOTKEY: Ctrl+R detected! Restarting ACIsstant...")
                os.kill(os.getpid(), signal.SIGTERM)
                break
        import time
        time.sleep(0.1)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the hotkey watcher thread
    t = threading.Thread(target=terminal_watcher, daemon=True)
    t.start()
    yield

app = FastAPI(title="ACIsstant Local AI Engineering Assistant", lifespan=lifespan)

# CORS for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve Frontend
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
async def read_index():
    return FileResponse("frontend/index.html")

# Managers
db = ChatDB()
llm_manager = LLMManager()
rag_manager = RAGManager()

# --- Models ---
class ChatRequest(BaseModel):
    chat_id: str
    message: str
    language: Optional[str] = "en-US"

# --- Endpoints ---

@app.get("/api/chats")
async def get_chats():
    return db.get_chats()

@app.post("/api/chats")
async def create_chat(title: str = Form("New Chat")):
    chat_id = str(uuid.uuid4())
    db.create_chat(chat_id, title)
    return {"chat_id": chat_id, "title": title}

@app.get("/api/chats/{chat_id}/messages")
async def get_messages(chat_id: str):
    return db.get_messages(chat_id)

def log_step(step_name: str, indent: int = 0):
    prefix = "  " * indent
    print(f"{prefix}[..] {step_name}")

@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    chat_id = request.chat_id
    user_msg = request.message

    log_step(f"Request: {str(user_msg)[:50]}...") # type: ignore
    
    # Store user message
    db.add_message(chat_id, "user", user_msg)
    
    past_messages = db.get_messages(chat_id)

    # File Inventory Awareness
    upload_dir = Path("data/uploads")
    all_files = [f.name for f in upload_dir.rglob("*") if f.is_file() and f.name != "README.md"]
    if request.language == "pt-PT":
        inventory_msg = f"Tens {len(all_files)} ficheiros disponíveis na tua base de dados: " + ", ".join(all_files) if all_files else "Não tens ficheiros carregados na base de dados."
    else:
        inventory_msg = f"You have {len(all_files)} files available in your knowledge base: " + ", ".join(all_files) if all_files else "No files are currently in your knowledge base."

    # RAG Retrieval
    log_step("Retrieving context from RAG...", 1)
    try:
        context = rag_manager.query(user_msg)
        log_step("Context retrieved.", 1)
    except Exception as e:
        print(f"  [!!] RAG Error: {str(e)}")
        context = ""
    
    # Prepare messages for LLM
    system_prompt = llm_manager.get_system_prompt(request.language)
    system_prompt += f"\n\n[INFO] {inventory_msg}"
    
    if context:
        if request.language == "pt-PT":
            system_prompt += f"\n\nContexto dos teus materiais de estudo:\n{context}"
        else:
            system_prompt += f"\n\nContext from your study materials:\n{context}"
    
    llm_messages = [{"role": "system", "content": system_prompt}] + past_messages[-10:] # Context window limit
    
    async def event_generator():
        full_response = ""
        log_step("Starting LLM stream...", 1)
        try:
            for token in llm_manager.generate_stream(llm_messages):
                full_response += token
                yield f"{token}"
            log_step("LLM Stream complete.", 1)
        except Exception as e:
            print(f"  [!!] LLM Stream Error: {str(e)}")
            yield f"\nERROR: {str(e)}"
        
        # Once stream is complete, store the assistant response
        db.add_message(chat_id, "assistant", full_response)

    return StreamingResponse(event_generator(), media_type="text/plain")

@app.put("/api/chats/{chat_id}")
async def rename_chat(chat_id: str, title: str = Form(...)):
    db.update_chat_title(chat_id, title)
    return {"status": "renamed", "title": title}

@app.delete("/api/chats/{chat_id}")
async def delete_chat(chat_id: str):
    db.delete_chat(chat_id)
    return {"status": "deleted"}

@app.post("/api/upload")
async def upload_docs(files: List[UploadFile] = File(...)):
    import shutil
    from pathlib import Path
    
    upload_dir = Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    saved_files = []
    for f in files:
        file_path = upload_dir / f.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(f.file, buffer)
        saved_files.append(f.filename)
        
    try:
        rag_manager.process_documents()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing error: {str(e)}")
        
    return {"status": "success", "files": saved_files}

@app.get("/api/files")
async def list_uploaded_files():
    from pathlib import Path
    upload_dir = Path("data/uploads")
    if not upload_dir.exists():
        return []
    
    files = []
    for f in upload_dir.rglob("*"):
        if f.is_file() and f.name != "README.md":
            files.append({
                "name": f.name,
                "path": str(f.relative_to(Path("data/uploads"))).replace("\\", "/"),
                "extension": f.suffix.lower().replace(".", "")
            })
    return files

@app.get("/api/files/download/{filename:path}")
async def download_file(filename: str):
    from fastapi.responses import FileResponse
    file_path = Path("data/uploads") / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)

@app.post("/api/rag/index")
async def trigger_index():
    try:
        rag_manager.process_documents()
        return {"status": "success", "message": "Documents indexed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/restart")
async def restart_server():
    log_step("API: Restart signal received.")
    import os
    import signal
    os.kill(os.getpid(), signal.SIGTERM)
    return {"status": "restarting"}

if __name__ == "__main__":
    import uvicorn # type: ignore
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        access_log=False,
        log_level="warning",
    )
