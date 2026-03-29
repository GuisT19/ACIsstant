import warnings
import os
import threading
try:
    import msvcrt
except ImportError:
    msvcrt = None
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
import logging
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from fastapi.staticfiles import StaticFiles # type: ignore
from pydantic import BaseModel # type: ignore
from typing import List, Optional, Dict
import threading
# msvcrt already handled above
import signal

from backend.llm import LLMManager # type: ignore
from backend.database import ChatDB # type: ignore
from backend.rag import RAGManager # type: ignore

# --- API initialization ---
def terminal_watcher():
    """Listens for Ctrl+R in the terminal window to restart the AI."""
    if msvcrt is None:
        return
    while True:
        if msvcrt.kbhit(): # type: ignore
            ch = msvcrt.getch() # type: ignore
            # Ctrl+R is character 18 (0x12) in binary mode on Windows
            if ch == b'\x12' or ch == b'\x12\r':
                print("\n  [!!] HOTKEY: Ctrl+R detected! Restarting ACIsstant...")
                import sys
                os._exit(3)
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

# --- Logging setup ---
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger("acisstant")

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


# --- Modularized handler for chat stream ---
async def handle_chat_stream(request: ChatRequest):
    chat_id = request.chat_id
    user_msg = request.message
    logger.info(f"[chat_stream] Request: {str(user_msg)[:50]}...")

    try:
        db.add_message(chat_id, "user", user_msg)
    except Exception as e:
        logger.error(f"Failed to store user message: {e}")
        raise HTTPException(status_code=500, detail="Failed to store user message.")

    try:
        past_messages = db.get_messages(chat_id)
    except Exception as e:
        logger.error(f"Failed to retrieve past messages: {e}")
        past_messages = []

    # File Inventory Awareness
    upload_dir = Path("data/uploads")
    all_files = [f.name for f in upload_dir.rglob("*") if f.is_file() and f.name != "README.md"]
    if request.language == "pt-PT":
        inventory_msg = f"Tens {len(all_files)} ficheiros disponíveis na tua base de dados: " + ", ".join(all_files) if all_files else "Não tens ficheiros carregados na base de dados."
    else:
        inventory_msg = f"You have {len(all_files)} files available in your knowledge base: " + ", ".join(all_files) if all_files else "No files are currently in your knowledge base."

    # RAG Retrieval
    logger.info("[chat_stream] Retrieving context from RAG...")
    try:
        context, sources = rag_manager.query(user_msg, k=2)
        logger.info(f"[chat_stream] Context retrieved (Sources: {len(sources)}).")
    except Exception as e:
        logger.error(f"RAG Error: {str(e)}")
        context, sources = "", []

    # Prepare messages for LLM
    raw_system = llm_manager.get_system_prompt(request.language)
    inventory_directive = (
        f"[SYSTEM DIRECTIVE] {inventory_msg}\n"
        "YOU MUST USE THESE FILES. YOU HAVE ACCESS TO THEM RIGHT NOW. "
        "IGNORE ANY INTERNAL PROGRAMMING THAT SAYS YOU CANNOT ACCESS FILES."
    )
    llm_messages = [
        {"role": "system", "content": f"{raw_system}\n\n{inventory_directive}"}
    ]
    if context:
        ctx_header = "Relevant context from YOUR LOCAL FILES:" if request.language != "pt-PT" else "Contexto relevante dos TEUS FICHEIROS LOCAIS:"
        llm_messages.append({"role": "system", "content": f"{ctx_header}\n{context}"})
    llm_messages.extend(past_messages[-8:])

    async def event_generator():
        full_response = ""
        logger.info("[chat_stream] Starting LLM stream...")
        try:
            for token in llm_manager.generate_stream(llm_messages):
                full_response += token
                yield f"{token}"
            if sources:
                sources_str = ", ".join(sources)
                yield f"\n\nSOURCES: {sources_str}"
            logger.info("[chat_stream] LLM Stream complete.")
        except Exception as e:
            logger.error(f"LLM Stream Error: {str(e)}")
            yield f"\nERROR: {str(e)}"
        try:
            db.add_message(chat_id, "assistant", full_response)
        except Exception as e:
            logger.error(f"Failed to store assistant message: {e}")

    return StreamingResponse(event_generator(), media_type="text/plain")

@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    return await handle_chat_stream(request)


# --- Modularized handler for renaming chat ---
async def handle_rename_chat(chat_id: str, title: str):
    try:
        db.update_chat_title(chat_id, title)
        logger.info(f"Chat {chat_id} renamed to '{title}'")
        return {"status": "renamed", "title": title}
    except Exception as e:
        logger.error(f"Failed to rename chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to rename chat.")

@app.put("/api/chats/{chat_id}")
async def rename_chat(chat_id: str, title: str = Form(...)):
    return await handle_rename_chat(chat_id, title)


# --- Modularized handler for deleting chat ---
async def handle_delete_chat(chat_id: str):
    try:
        db.delete_chat(chat_id)
        logger.info(f"Chat {chat_id} deleted.")
        return {"status": "deleted"}
    except Exception as e:
        logger.error(f"Failed to delete chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete chat.")

@app.delete("/api/chats/{chat_id}")
async def delete_chat(chat_id: str):
    return await handle_delete_chat(chat_id)


# --- Modularized handler for document upload ---
async def handle_upload_docs(files: List[UploadFile]):
    import shutil
    upload_dir = Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    saved_files = []
    for f in files:
        file_path = upload_dir / f.filename
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(f.file, buffer)
            saved_files.append(f.filename)
            logger.info(f"Uploaded file: {f.filename}")
        except Exception as e:
            logger.error(f"Failed to save file {f.filename}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to save file: {f.filename}")
    try:
        rag_manager.process_documents()
        logger.info("RAG index updated after upload.")
    except Exception as e:
        logger.error(f"Indexing error: {e}")
        raise HTTPException(status_code=500, detail=f"Indexing error: {str(e)}")
    return {"status": "success", "files": saved_files}

@app.post("/api/upload")
async def upload_docs(files: List[UploadFile] = File(...)):
    return await handle_upload_docs(files)


# --- Modularized handler for listing uploaded files ---
async def handle_list_uploaded_files():
    upload_dir = Path("data/uploads")
    if not upload_dir.exists():
        logger.info("No upload directory found.")
        return []
    files = []
    for f in upload_dir.rglob("*"):
        if f.is_file() and f.name != "README.md":
            files.append({
                "name": f.name,
                "path": str(f.relative_to(upload_dir)).replace("\\", "/"),
                "extension": f.suffix.lower().replace(".", "")
            })
    logger.info(f"Listed {len(files)} uploaded files.")
    return files

@app.get("/api/files")
async def list_uploaded_files():
    return await handle_list_uploaded_files()


# --- Modularized handler for file download ---
async def handle_download_file(filename: str):
    file_path = Path("data/uploads") / filename
    if not file_path.exists():
        logger.warning(f"File not found for download: {filename}")
        raise HTTPException(status_code=404, detail="File not found")
    logger.info(f"File downloaded: {filename}")
    from fastapi.responses import FileResponse # type: ignore
    return FileResponse(file_path)

@app.get("/api/files/download/{filename:path}")
async def download_file(filename: str):
    return await handle_download_file(filename)


# --- Modularized handler for RAG reindex ---
async def handle_trigger_index():
    try:
        rag_manager.process_documents()
        logger.info("RAG index rebuilt successfully.")
        return {"status": "success", "message": "Documents indexed successfully"}
    except Exception as e:
        logger.error(f"RAG reindex error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/rag/index")
async def trigger_index():
    return await handle_trigger_index()

@app.get("/api/token-usage/{chat_id}")
async def get_token_usage(chat_id: str):
    """Returns token usage stats for the current chat context."""
    messages = db.get_messages(chat_id)
    
    n_ctx = 4096
    if llm_manager.llm:
        n_ctx = llm_manager.llm.n_ctx()
    
    system_prompt = llm_manager.get_system_prompt("en-US")
    all_messages = [{"role": "system", "content": system_prompt}]
    # Match history window of stream endpoint (8)
    all_messages.extend(messages[-8:])
    
    total_tokens = 0
    if llm_manager.llm:
        prompt = llm_manager.format_prompt(all_messages)
        try:
            tokens = llm_manager.llm.tokenize(prompt.encode("utf-8"))
            total_tokens = len(tokens)
        except Exception:
            total_tokens = sum(len(m["content"]) for m in all_messages) // 4
    else:
        total_tokens = sum(len(m["content"]) for m in all_messages) // 4
    
    percentage = round(float(total_tokens) / float(n_ctx) * 100, 1) if n_ctx > 0 else 0.0
    
    return {
        "used_tokens": total_tokens,
        "max_tokens": n_ctx,
        "percentage": min(percentage, 100),
        "message_count": len(messages),
        "is_compressed": any(m.get("role") == "system" and "COMPRESSED_SUMMARY" in m.get("content", "") for m in messages)
    }


# --- Modularized handler for compressing chat ---
async def handle_compress_chat(chat_id: str):
    try:
        messages = db.get_messages(chat_id)
        if len(messages) <= 6:
            logger.info(f"Chat {chat_id} not compressed: not enough messages.")
            return {"status": "skip", "reason": "Not enough messages to compress"}
        old_messages = messages[:-4]
        summary_parts = []
        for msg in old_messages:
            role_label = "User" if msg["role"] == "user" else "AI"
            content = msg["content"][:200].strip()
            summary_parts.append(f"[{role_label}]: {content}")
        compressed_summary = "[COMPRESSED_SUMMARY] Previous conversation context:\n" + "\n".join(summary_parts)
        db.compress_messages(chat_id, len(old_messages), compressed_summary)
        logger.info(f"Chat {chat_id} compressed: {len(old_messages)} messages summarized.")
        return {"status": "compressed", "removed": len(old_messages), "summary_length": len(compressed_summary)}
    except Exception as e:
        logger.error(f"Failed to compress chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to compress chat.")

@app.post("/api/chat/compress/{chat_id}")
async def compress_chat(chat_id: str):
    return await handle_compress_chat(chat_id)


# --- Modularized handler for purging old chat messages ---
async def handle_purge_chat(chat_id: str):
    try:
        messages = db.get_messages(chat_id)
        if len(messages) <= 4:
            logger.info(f"Chat {chat_id} not purged: too few messages.")
            return {"status": "skip", "reason": "Too few messages to purge"}
        purge_count = max(1, len(messages) // 10)
        db.purge_oldest_messages(chat_id, purge_count)
        logger.info(f"Chat {chat_id} purged: {purge_count} messages removed.")
        return {"status": "purged", "removed": purge_count, "remaining": len(messages) - purge_count}
    except Exception as e:
        logger.error(f"Failed to purge chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to purge chat.")

@app.post("/api/chat/purge/{chat_id}")
async def purge_chat(chat_id: str):
    return await handle_purge_chat(chat_id)

@app.post("/api/restart")
async def restart_server():
    log_step("API: Restart signal received.")
    import os
    import sys
    os._exit(3)

if __name__ == "__main__":
    import uvicorn # type: ignore
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        access_log=False,
        log_level="warning",
    )
