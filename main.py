from telethon.sync import TelegramClient
from telethon import events
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import os
from dotenv import load_dotenv

# =======================
# LOAD ENV VARIABLES
# =======================
load_dotenv()
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

SESSION_DIR = "sessions"
if not os.path.exists(SESSION_DIR):
    os.makedirs(SESSION_DIR)

app = FastAPI()

# =======================
# DATA MODELS
# =======================
class LoginRequest(BaseModel):
    phone: str

class CodeRequest(BaseModel):
    phone: str
    code: str

class ConfigRequest(BaseModel):
    phone: str
    source_chat: int
    dest_chat: int
    filters: list[str]  # Example: ["text", "photo", "video", "link"]

# =======================
# IN-MEMORY STORAGE
# =======================
clients = {}        # Active Telegram clients
configs = {}        # Per-user forwarding config
otp_hashes = {}     # Store phone_code_hash temporarily

# =======================
# TELEGRAM SESSION HELPER
# =======================
def get_client(phone):
    session_path = os.path.join(SESSION_DIR, phone)
    return TelegramClient(session_path, API_ID, API_HASH)

# =======================
# LOGIN ENDPOINT
# =======================
@app.post("/login")
async def login(req: LoginRequest):
    client = get_client(req.phone)
    await client.connect()

    if not await client.is_user_authorized():
        sent = await client.send_code_request(req.phone)
        otp_hashes[req.phone] = sent.phone_code_hash
        return {"status": "code_sent"}

    clients[req.phone] = client
    return {"status": "already_logged_in"}

# =======================
# VERIFY OTP ENDPOINT
# =======================
@app.post("/verify")
async def verify(req: CodeRequest):
    client = get_client(req.phone)
    await client.connect()

    try:
        code_hash = otp_hashes.get(req.phone)
        if not code_hash:
            return {"status": "error", "detail": "phone_code_hash missing"}

        await client.sign_in(phone=req.phone, code=req.code, phone_code_hash=code_hash)
        clients[req.phone] = client
        otp_hashes.pop(req.phone, None)
        return {"status": "logged_in"}

    except Exception as e:
        return {"status": "error", "detail": str(e)}

# =======================
# START FORWARDING ENDPOINT
# =======================
@app.post("/start")
async def start_forwarding(req: ConfigRequest):
    client = clients.get(req.phone)
    if not client:
        return {"error": "Client not logged in"}

    configs[req.phone] = req

    @client.on(events.NewMessage(chats=[req.source_chat]))
    async def handler(event):
        msg = event.message
        if should_forward(msg, req.filters):
            await client.send_message(req.dest_chat, msg)

    await client.start()
    return {"status": "forwarding_started"}

# =======================
# STATUS ENDPOINT
# =======================
@app.get("/status/{phone}")
async def status(phone: str):
    return {
        "logged_in": phone in clients,
        "forwarding": phone in configs
    }

# =======================
# FILTER LOGIC
# =======================
def should_forward(msg, filters):
    if "text" in filters and msg.text:
        return True
    if "photo" in filters and msg.photo:
        return True
    if "video" in filters and msg.video:
        return True
    if "link" in filters and msg.entities:
        for e in msg.entities:
            if hasattr(e, 'url') or (hasattr(e, 'type') and e.type == 'url'):
                return True
    return False

# =======================
# RUN SERVER (DEV ONLY)
# =======================
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
