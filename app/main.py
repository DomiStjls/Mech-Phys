from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

import uuid
import base64
import math
import copy
from app.logic.elements import generate_svg_for_object, generate_anchors_for_plane
from app.logic.params import save_params, load_params, save_scene, load_scene

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="Domik")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


def short_uuid_base64():
    u = uuid.uuid4()
    return base64.urlsafe_b64encode(u.bytes).rstrip(b"=").decode("ascii")


@app.get("/favicon.ico")
def favicon(request: Request):
    return FileResponse("./favicon.ico")


@app.get("/", response_class=HTMLResponse)
async def get_main_page(request: Request):
    scene = load_scene()
    svg_elements = [generate_svg_for_object(obj) for obj in scene.get("objects", [])]

    # Инициализация режима и параметров, если они не существуют
    if "mode" not in request.session:
        request.session["mode"] = "plane"

    params = load_params()
    print(params)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "scene": scene,
            "svg_elements": svg_elements,
            "mode": request.session["mode"],
            "params": params,
        },
    )


@app.post("/set_params")
async def set_params(request: Request):
    data = await request.json()
    params = load_params()

    # Обновляем только переданные параметры
    for key, value in data.items():
        if key in params:
            params[key] = value
    save_params(params)
    return {"status": "ok"}


@app.post("/set_mode")
async def set_mode(request: Request, mode: str = Form(...)):
    request.session["mode"] = mode
    return {"status": "ok"}


@app.post("/add_object")
async def add_object(
    request: Request,
):
    data = await request.json()
    scene = load_scene()
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
            "id": str(short_uuid_base64()),
            "x_center": int(
                x + 0.5 * int(data["length"]) * math.cos(math.radians(angle))
            ),
            "y_center": int(
                y - 0.5 * int(data["length"]) * math.sin(math.radians(angle))
            ),
        }
        anchors = generate_anchors_for_plane(obj, 80)
        scene["objects"].extend(anchors)
    elif type == "block":
        width = int(data["width"])
        height = int(data["height"])
        obj = {
            "type": "block",
            "x_0": x,
            "y_0": y,
            "width": width,
            "height": height,
            "id": str(short_uuid_base64()),
            "x_center": int(x + 0.5 * width),
            "y_center": int(y + 0.5 * height),
            "angle": 0,
        }
    elif type == "string":
        attachment = data["attachment"]
        obj = {
            "type": "string",
            "attachment": attachment,
            "id": str(short_uuid_base64()),
            "x_0": x,
            "y_0": y,
            "angle": 0,
        }

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
        "id": str(short_uuid_base64()),
    }
    scene["relations"].append(relation)
    scene["history"].append({"action": "add_relation", "relation": relation})
    save_scene(scene)
    return {"status": "relation added", "relation": relation}


@app.post("/undo")
async def undo(request: Request):
    scene = load_scene()
    scene["history"].pop()
    object = scene["objects"].pop()
    if object["type"] == "plane":
        scene_copy = [
            el
            for el in copy.deepcopy(scene["objects"])
            if not (
                el["type"] == "anchor" and el.get("parent_id", None) == object["id"]
            )
        ]
        scene["objects"] = copy.deepcopy(scene_copy)

    save_scene(scene)
    return {"status": "ok"}


@app.post("/clear")
async def clear(request: Request):
    scene = load_scene()
    save_scene(scene)
    return {"status": "ok"}
