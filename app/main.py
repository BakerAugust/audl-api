from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/")
async def root():
    return {"message": "How about now?"}


@app.get("/items/landing", response_class=HTMLResponse)
async def read_item(request: Request):
    print(request)
    return templates.TemplateResponse("items/landing.html", {"request": request})


@app.get("/items/edit", response_class=HTMLResponse)
async def edit_item(request: Request):
    print(request)
    return templates.TemplateResponse("items/edit.html", {"request": request})

