from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import uuid
import math
import json
import os
from app.logic.elements import generate_svg_for_object

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="Domik")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

SCENE_PATH = "data/scene.json"


def load_scene():
    if os.path.exists(SCENE_PATH):
        with open(SCENE_PATH, "r") as f:
            return json.load(f)
    return {
        "objects": [],
        "relations": [],
        "history": [],
        "mode": "",
        # "svg_objects": [],
    }


def save_scene(scene):
    os.makedirs(os.path.dirname(SCENE_PATH), exist_ok=True)
    with open(SCENE_PATH, "w") as f:
        json.dump(scene, f)


@app.get("/", response_class=HTMLResponse)
async def get_main_page(request: Request):
    scene = load_scene()
    svg_elements = [generate_svg_for_object(obj) for obj in scene.get("objects", [])]
    if 'mode' not in request.session:
        request.session['mode'] = 'plane'
    print(request.session['mode'])
    return templates.TemplateResponse(
        "index.html", {"request": request, "scene": scene, "svg_elements": svg_elements, 'mode': request.session["mode"]}
    )


@app.post("/set_mode")
async def set_mode(request: Request, mode: str = Form(...)):
    
    request.session["mode"] = mode
    return {"status": "ok"}


@app.post("/add_object")
async def add_object(
    request: Request,
):
    data = await request.json()
    x, y, type = int(data["x"]), int(data["y"]), data["type"]
    if type == "plane":
        angle = int(data["angle"])
        length = int(data["length"])
        obj = {
            "type": "plane",
            "x_0": x,
            "y_0": y,
            "length": length,
            "angle": angle,
            "id": str(uuid.uuid4()),
            "x_center": int(
                x + 0.5 * int(data["length"]) * math.cos(math.radians(angle))
            ),
            "y_center": int(
                y - 0.5 * int(data["length"]) * math.sin(math.radians(angle))
            ),
        }
    elif type == "block":
        width = int(data["width"])
        height = int(data["height"])
        obj = {
            "type": "block",
            "x_0": x,
            "y_0": y,
            "width": width,
            "height": height,
            "id": str(uuid.uuid4()),
            "x_center": int(x + 0.5 * width),
            "y_center": int(y + 0.5 * height),
            "angle": 0,
        }
    elif type == "string":
        attachment = data["attachment"]
        obj = {
            "type": "string",
            "attachment": attachment,
            "id": str(uuid.uuid4()),
            "x_0": x,
            "y_0": y,
            "angle": 0,
        }

    scene = load_scene()
    # scene["svg_objects"].append(generate_svg_for_object(obj))
    # print(len(scene["svg_objects"]))
    scene["objects"].append(obj)
    scene["history"].append({"action": "add", "object": obj})
    save_scene(scene)
    return {"status": "added", "object": obj}


@app.post("/add_relation")
async def add_relation(
    request: Request,
):
    data = await request.json()
    source_id = data["source"]
    target_id = data["target"]
    relation_type = data["type"]
    scene = load_scene()
    relation = {
        "source": source_id,
        "target": target_id,
        "type": relation_type,
        "id": str(uuid.uuid4()),
    }
    scene["relations"].append(relation)
    scene["history"].append({"action": "add_relation", "relation": relation})
    save_scene(scene)
    return {"status": "relation added", "relation": relation}


@app.post("/undo")
async def undo(request: Request):
    scene = load_scene()
    scene["history"].pop()
    scene["objects"].pop()
    save_scene(scene)
    return {"status": "ok"}


@app.post("/clear")
async def clear(request: Request):
    
    scene = {
        "objects": [],
        "relations": [],
        "history": [],
        "mode": "",  # текущий выбранный режим
    }
    save_scene(scene)
    return {"status": "ok"}
