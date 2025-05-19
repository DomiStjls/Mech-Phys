from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# from app.logic.elements import Block, Force

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

scene = []  # временное хранилище объектов

@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    # svg_elements = [obj.to_svg() for obj in scene]
    return templates.TemplateResponse("index.html", {
        "request": request,
        "svg_elements": scene
    })

@app.post("/add_block_by_nodes")
async def add_block_by_nodes(request: Request):
    data = await request.json()
    x1, y1, x2, y2 = map(int, (data["x1"], data["y1"], data["x2"], data["y2"]))

    block_svg = f'<rect x="{min(x1, x2)}" y="{min(y1, y2)}" width="{abs(x2 - x1)}" height="{abs(y2 - y1)}" fill="green" fill-opacity="0.4" stroke="black" />'
    scene.append(block_svg)
    return JSONResponse(content={"status": "ok"})

@app.post("/clear")
async def clear(request: Request):
    scene.clear()
    return JSONResponse(content={"status": "ok"})