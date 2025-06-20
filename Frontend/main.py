from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import httpx

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Store session in memory (not production safe)
session_data = {}

BACKEND_URL = "https://autoforward-nbf4.onrender.com"

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "step": "phone"})

@app.post("/send-phone", response_class=HTMLResponse)
async def send_phone(request: Request, phone: str = Form(...)):
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{BACKEND_URL}/login", json={"phone": phone})
        data = res.json()
    session_data["phone"] = phone
    return templates.TemplateResponse("index.html", {"request": request, "step": "otp", "message": data.get("status")})

@app.post("/verify-otp", response_class=HTMLResponse)
async def verify_otp(request: Request, code: str = Form(...)):
    phone = session_data.get("phone")
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{BACKEND_URL}/verify", json={"phone": phone, "code": code})
        data = res.json()
    return templates.TemplateResponse("index.html", {"request": request, "step": "config", "message": data.get("status")})

@app.post("/start-forward", response_class=HTMLResponse)
async def start_forwarding(
    request: Request,
    source_chat: int = Form(...),
    dest_chat: int = Form(...),
    filters: str = Form(...)
):
    phone = session_data.get("phone")
    filters_list = [f.strip() for f in filters.split(",")]
    payload = {
        "phone": phone,
        "source_chat": source_chat,
        "dest_chat": dest_chat,
        "filters": filters_list
    }
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{BACKEND_URL}/start", json=payload)
        data = res.json()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "step": "done",
        "message": data.get("status")
    })
