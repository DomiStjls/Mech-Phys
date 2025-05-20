from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import math
# from app.logic.elements import Block, Force

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

scene = []  # временное хранилище объектов
objects = []
relations = []
k = 0
d = 20


@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    # svg_elements = [obj.to_svg() for obj in scene]
    print(scene, objects, relations)
    return templates.TemplateResponse(
        "index.html", {"request": request, "svg_elements": scene}
    )


@app.post("/add_block_by_nodes")
async def add_block_by_nodes(request: Request):
    global k
    data = await request.json()
    x1, y1, x2, y2 = map(int, (data["x1"], data["y1"], data["x2"], data["y2"]))

    block_svg = f'<rect x="{min(x1, x2)}" y="{min(y1, y2)}" width="{abs(x2 - x1)}" height="{abs(y2 - y1)}" fill="green" fill-opacity="0.4" stroke="black" />'
    scene.append(block_svg)
    objects.append({"type": "block", "x1": x1, "y1": y1, "x2": x2, "y2": y2, "id": k})
    k += 1
    return JSONResponse(content={"status": "ok"})


@app.post("/add_plane_by_nodes")
async def add_plane_by_nodes(request: Request):
    global k
    data = await request.json()
    x1, y1, x2, y2 = map(int, (data["x1"], data["y1"], data["x2"], data["y2"]))

    plane = f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="black" stroke-width="3" />'

    scene.append(plane)
    objects.append(
        {
            "type": "plane",
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
            "angle": math.degrees(math.atan2(abs(y2 - y1), abs(x2 - x1))),
            "id": k,
        }
    )
    k += 1
    return JSONResponse(content={"status": "ok"})


@app.post("/add_string_by_nodes")
async def add_string_by_nodes(request: Request):
    global k
    data = await request.json()
    x1, y1, x2, y2 = map(int, (data["x1"], data["y1"], data["x2"], data["y2"]))

    string = f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="grey" stroke-width="3" />'

    scene.append(string)
    objects.append(
        {
            "type": "string",
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
            "angle": math.degrees(math.atan2(abs(y2 - y1), abs(x2 - x1))),
            "id": k,
        }
    )
    k += 1
    return JSONResponse(content={"status": "ok"})


@app.post("/add_block_on_plane")
async def add_block_on_plane(request: Request):
    global k
    data = await request.json()
    print(data)
    x1, y1, h, w = map(int, (data["x"], data["y"], data["height"], data["width"]))
    h = h * d
    w = w * d
    # поиск плоскости для блока
    flag = False
    for obj in objects:
        if obj["type"] == "plane" and (
            obj["angle"] == 0
            or abs((x1 - obj["x1"]) / (y1 - obj["y1"]))
            == abs((obj["x2"] - obj["x1"]) / (obj["y2"] - obj["y1"]))
        ):
            angle_deg = obj["angle"]
            flag = True
    if not flag:
        return JSONResponse(
            content={
                "status": "error",
                "message": "плоскость не найдена, укажите точку начала груза на плоскости",
            }
        )
    else:
        relations.append(
            {
                "object1": "plane",
                "object2": "block on plane",
                "id1": obj["id"],
                "id2": k,
            }
        )

    block_svg = f'<rect x="{x1}" y="{y1 - h}" width="{w}" height="{h}" fill="green" fill-opacity="0.4" stroke="black"  transform="rotate({angle_deg}, {x1}, {y1})" />'
    scene.append(block_svg)
    objects.append(
        {
            "type": "block on plane",
            "x1": x1,
            "y1": y1,
            "x2": x1 + w,
            "y2": y1 + h,
            "id": k,
        }
    )
    k += 1
    return JSONResponse(content={"status": "ok"})


@app.post("/clear")
async def clear(request: Request):
    scene.clear()
    return JSONResponse(content={"status": "ok"})
