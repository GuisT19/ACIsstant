import os
import uuid
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict

from backend.llm import LLMManager
from backend.database import ChatDB
from backend.rag import RAGManager

# --- API initialization ---
app = FastAPI(title="Antigravity Local AI Engineering Assistant")

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
    from fastapi.responses import FileResponse
    return FileResponse("frontend/index.html")

# Managers
db = ChatDB()
llm_manager = LLMManager()
rag_manager = RAGManager()

# --- Models ---
class ChatRequest(BaseModel):
    chat_id: str
    message: str
    language: Optional[str] = "pt-PT"

# --- Endpoints ---

@app.get("/api/chats")
async def get_chats():
    return db.get_chats()

@app.post("/api/chats")
async def create_chat(title: str = Form("Novo Chat")):
    chat_id = str(uuid.uuid4())
    db.create_chat(chat_id, title)
    return {"chat_id": chat_id, "title": title}

@app.get("/api/chats/{chat_id}/messages")
async def get_messages(chat_id: str):
    return db.get_messages(chat_id)

@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    chat_id = request.chat_id
    user_msg = request.message
    
    # Check if chat exists
    # we could verify if chat exists in DB, but for now we trust the ID

    # Store user message
    db.add_message(chat_id, "user", user_msg)
    
    past_messages = db.get_messages(chat_id)

    # RAG Retrieval
    context = rag_manager.query(user_msg)
    
    # Prepare messages for LLM
    # include system prompt, RAG context and last few messages for context
    system_prompt = llm_manager.get_system_prompt(request.language)
    
    if context:
        system_prompt += f"\n\nContexto dos teus materiais de estudo:\n{context}"
    
    llm_messages = [{"role": "system", "content": system_prompt}] + past_messages[-10:] # Context window limit
    
    async def event_generator():
        full_response = ""
        for token in llm_manager.generate_stream(llm_messages):
            full_response += token
            yield f"{token}"
        
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

@app.post("/api/rag/index")
async def trigger_index():
    try:
        rag_manager.process_documents()
        return {"status": "success", "message": "Documents indexed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
