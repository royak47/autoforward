from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn

app = FastAPI()

# Template and static folder config
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/download", response_class=HTMLResponse)
async def download(request: Request, url: str = Form(...)):
    # 🧠 Dummy result — replace with real logic (like hitting your /getlink)
    result = None
    if "instagram.com" in url or "youtu" in url:
        # Here you can call your internal API or downloader logic
        result = f"✅ Download started for: {url}"
    else:
        result = "❌ Unsupported or invalid URL"

    return templates.TemplateResponse("index.html", {
        "request": request,
        "result": result
    })

if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)
