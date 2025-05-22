from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import math

from starlette.middleware.sessions import SessionMiddleware

# from app.logic.elements import Block, Force

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key="supersecretkey")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# scene = []  # временное хранилище объектов
# objects = []
# relations = []
k = 0
d = 20

favicon_path = "favicon.ico"


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(favicon_path)


@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    scene = request.session.get("scene", [])
    objects = request.session.get("objects", {})
    relations = request.session.get("relations", [])
    request.session["scene"] = scene
    request.session["objects"] = objects
    request.session["relations"] = relations
    #print(scene, objects, relations)
    return templates.TemplateResponse(
        "index.html", {"request": request, "svg_elements": scene}
    )


@app.post("/add_block_by_nodes")
async def add_block_by_nodes(request: Request):
    global k
    data = await request.json()
    x1, y1, x2, y2 = map(int, (data["x1"], data["y1"], data["x2"], data["y2"]))

    block_svg = f'''
    <g id="{k}" class="svg-object" data-id="{k}" data-type="block">
        <rect x="{min(x1, x2)}" y="{min(y1, y2)}" width="{abs(x2 - x1)}" height="{abs(y2 - y1)}"
            fill="green" fill-opacity="0.4" stroke="black" />
    </g>
    '''
    request.session["scene"].append(block_svg)
    
    request.session["objects"][str(k)] = {
        "type": "block",
        "x1": x1,
        "y1": y1,
        "x2": x2,
        "y2": y2,
        "id": k,
    }

    k += 1
    return JSONResponse(content={"status": "ok"})


@app.post("/add_plane_by_nodes")
async def add_plane_by_nodes(request: Request):
    global k
    data = await request.json()
    x1, y1, x2, y2 = map(int, (data["x1"], data["y1"], data["x2"], data["y2"]))

    # plane = f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="black" stroke-width="3" />'
    block_svg = f'''
    <g id="{k}" class="svg-object" data-id="{k}" data-type="plane">
        <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="black" stroke-width="5" />
    </g>
    '''
    request.session["scene"].append(block_svg)

    request.session["objects"][str(k)] = {
        "type": "plane",
        "x1": x1,
        "y1": y1,
        "x2": x2,
        "y2": y2,
        "angle": math.degrees(math.atan2(abs(y2 - y1), abs(x2 - x1))),
        "id": k,
    }

    k += 1
    return JSONResponse(content={"status": "ok"})


@app.post("/add_string_by_nodes")
async def add_string_by_nodes(request: Request):
    global k
    data = await request.json()
    x1, y1, x2, y2 = map(int, (data["x1"], data["y1"], data["x2"], data["y2"]))

    # string = f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="grey" stroke-width="3" />'
    block_svg = f'''
    <g id="{k}" class="svg-object" data-id="{k}" data-type="string">
        <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="grey" stroke-width="3" />
    </g>
    '''
    request.session["scene"].append(block_svg)
    request.session["objects"][str(k)] = {
        "type": "string",
        "x1": x1,
        "y1": y1,
        "x2": x2,
        "y2": y2,
        "angle": math.degrees(math.atan2(abs(y2 - y1), abs(x2 - x1))),
        "id": k,
    }

    k += 1
    return JSONResponse(content={"status": "ok"})


@app.post("/add_block_on_object")
async def add_block_on_object(request: Request):
    global k
    data = await request.json()

    y1, h, w = map(int, (data["y"], data["height"], data["width"]))
    x1 = float(data["x"])
    id_object_for_rel = data["id"]
    type_object_for_rel = data["type"]
    print(x1, y1, h, w, id_object_for_rel, type_object_for_rel)
    h = h * d
    w = w * d
    obj = request.session["objects"].get(
        id_object_for_rel, {}
    )  # request.session["objects"][id_object_for_rel]
    print(obj)
    if not obj:
        return JSONResponse(content={"status": "error"})
    angle_deg = obj["angle"]
    request.session["relations"].append(
        {
            "object1": "plane",
            "object2": f"block on {type_object_for_rel}",
            "id1": obj["id"],
            "id2": k,
        }
    )
    a = math.radians(angle_deg)


    m = -1 if ((obj['x1'] - obj['x2'] > 0) == (obj['y1'] - obj['y2'] < 0)) else 1
    new_x = x1 + h * math.sin(a) * m  # + h * math.sin(a)
    new_y = y1 - h * math.cos(a)  # - w * math.sin(a)
    # block_svg = f'<rect x="{new_x}" y="{new_y}" width="{w}" height="{h}" fill="green" fill-opacity="0.4" stroke="black"  transform="rotate({-angle_deg}, {new_x}, {new_y})" />'
    block_svg = f'''
    <g id="{k}" class="svg-object" data-id="{k}" data-type="block-on-plane">
       <rect x="{new_x}" y="{new_y}" width="{w}" height="{h}" fill="green" fill-opacity="0.4" stroke="black"  transform="rotate({m * angle_deg}, {new_x}, {new_y})" />
    </g>
    '''
    request.session["scene"].append(block_svg)
    request.session["objects"][str(k)] = {
        "type": f"block on {type_object_for_rel}",
        "x1": x1,
        "y1": y1,
        "x2": x1 + w * math.cos(a) - h * math.sin(a),
        "y2": y1 - h * math.cos(a) - w * math.sin(a),
        "angle": angle_deg,
        "id": k,
    }
    k += 1
    return JSONResponse(content={"status": "ok"})


@app.post("/clear")
async def clear(request: Request):
    request.session["scene"].clear()
    request.session["objects"].clear()
    request.session["relations"].clear()
    request.session["scene"] = []
    request.session["objects"] = {}        
    request.session["relations"] = []
    return JSONResponse(content={"status": "ok"})


@app.post("/undo")
async def undo(request: Request):
    print(1)
    scene = request.session.get("scene", [])
    objects = request.session.get("objects", {})
    relations = request.session.get("relations", [])
    if scene:
        scene.pop()  # удаляем последний элемент
        request.session["scene"] = scene
        request.session["objects"] = objects
        request.session["relations"] = relations
    return RedirectResponse("/", status_code=303)
