from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

import uuid
import base64
import math
import copy
from app.logic.elements import (
    generate_svg_for_object,
    generate_anchors_for_plane,
    generate_anchors_for_block,
)
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
    svg_elements.extend(
        [generate_svg_for_object(obj) for obj in scene.get("anchors", {}).values()]
    )

    # Инициализация режима и параметров, если они не существуют
    if "mode" not in request.session:
        request.session["mode"] = "plane"

    params = load_params()
    # print(scene["objects"], scene["anchors"])
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
            # "x_center": int(
            #     x + 0.5 * int(data["length"]) * math.cos(math.radians(angle))
            # ),
            # "y_center": int(
            #     y - 0.5 * int(data["length"]) * math.sin(math.radians(angle))
            # ),
        }
        anchors = generate_anchors_for_plane(obj, 80)
        for el in anchors:
            scene["anchors"][el["id"]] = el
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
            "x_rotate": x,
            "y_rotate": y - height,
            "angle": 0,
        }
        anchors = generate_anchors_for_block(obj, 40)
        for el in anchors:
            scene["anchors"][el["id"]] = el
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


def create_relation(objects={}, relation_type="anchor"):
    # if relation_type == "string":
    #     pass
    # if relation_type == "anchor":
    #     main_anchor = objects["anchor"]
    pass


@app.post("/add_relation")
async def add_relation(
    request: Request,
):
    data = await request.json()
    scene = load_scene()
    x, y = map(int, (data["x"], data["y"]))
    id = data["anchor_id"]
    add = data["type_add"]
    anchor = scene["anchors"].get(id)
    nearest_anchor = anchor
    print(f"nearest anchor: {nearest_anchor}, data: {data}")
    obj_parent = [
        el for el in scene["objects"] if el["id"] == nearest_anchor["parent_id"]
    ][0]
    angle = obj_parent.get("angle", 0)
    if add == "plane" and obj_parent["type"] == "plane":
        if data["angle"] == angle:  # ошибка в пересечении объектов
            return {"status": "error in relation (intersection)"}
        obj = {
            "type": "plane",
            "x_0": nearest_anchor["x"],
            "y_0": nearest_anchor["y"],
            "length": int(data["length"]),
            "angle": int(data["angle"]),
            "id": str(short_uuid_base64()),
        }
        create_relation()
        anchors = generate_anchors_for_plane(obj, 80, no_first=True)
        for el in anchors:
            scene["anchors"][el["id"]] = el
        scene["objects"].append(obj)
        scene["history"].append({"action": "add", "object": obj})
    if add == "block" and obj_parent["type"] == "plane":
        # TODO пересечение объектов проверка
        x1, y1 = nearest_anchor["x"], nearest_anchor["y"]
        height = int(data["height"])
        angle = angle % 360
        if 0 <= angle < 90:
            m = -1
        elif 90 <= angle < 180:
            m = 1
        elif 180 <= angle < 270:
            m = -1
            angle = angle - 180
        elif 270 <= angle < 360:
            m = 1
            angle = 360 - angle
        a = math.radians(angle)
        rotate_x = x1 + height * math.sin(a) * m
        rotate_y = y1 - height * math.cos(a)

        # print(m, angle % 360)
        obj = {
            "type": "block",
            "x_0": x,
            "y_0": y,
            "width": int(data["width"]),
            "height": height,
            "id": str(short_uuid_base64()),
            "x_rotate": rotate_x,
            "y_rotate": rotate_y,
            "angle": angle * m,
        }
        create_relation()
        # TODO angles on block
        scene["objects"].append(obj)
        anchors = generate_anchors_for_block(obj, no_first=True)
        for el in anchors:
            scene["anchors"][el["id"]] = el
        scene["history"].append({"action": "add", "object": obj})
    if add == "string" and obj_parent["type"] == "plane":
        # TODO пересечение объектов проверка
        x1, y1 = nearest_anchor["x"], nearest_anchor["y"]
        attachment = data["attachment"]
    save_scene(scene)
    return {"status": "relation added"}


@app.post("/undo")
async def undo(request: Request):
    scene = load_scene()
    scene["history"].pop()
    object = scene["objects"].pop()
    anchors = {
        k: v
        for k, v in scene["anchors"].items()
        if not (v["parent_id"] == object["id"])
    }
    scene["anchors"] = copy.deepcopy(anchors)

    save_scene(scene)
    return {"status": "ok"}


@app.post("/clear")
async def clear(request: Request):
    scene = load_scene(clear=True)
    save_scene(scene)
    return {"status": "ok"}

@app.get("/clear")
async def clear_get(request: Request):
    scene = load_scene(clear=True)
    save_scene(scene)
    return {"status": "ok"}