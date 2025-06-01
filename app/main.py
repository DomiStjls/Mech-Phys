from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware


import math
import copy
from app.logic.elements import (
    generate_svg_for_object,
    generate_anchors_for_plane,
    generate_anchors_for_block,
)
from app.logic.features import (
    save_params,
    load_params,
    save_scene,
    load_scene,
    create_relation,
    find_relations_for_object,
    remove_object_from_relations,
    short_uuid_base64,
    
)

from app.logic.physics import analyze_forces_at_point, analyze_all_forces

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="Domik")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


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
    if "mode" not in request.session:
        request.session["mode"] = "plane"

    params = load_params()
    print(scene['objects'])
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
    for key, value in data.items():
        if key in params:
            params[key] = value
    save_params(params)
    return {"status": "ok"}


@app.post("/set_mode")
async def set_mode(request: Request, mode: str = Form(...)):
    request.session["mode"] = mode
    return {"status": "mode is changed"}


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
        return {"status": "not implemented"}

    scene["objects"].append(obj)

    scene["history"].append({"action": "add", "object": obj})
    save_scene(scene)
    return {"status": "added", "object": obj}


@app.post("/add_relation")
async def add_relation(
    request: Request,
):
    data = await request.json()
    scene = load_scene()
    id = data["anchor_id"]
    add = data["type_add"]
    anchor = scene["anchors"].get(id)
    nearest_anchor = anchor
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

        

        anchors = generate_anchors_for_plane(obj, 80, no_first=True)
        for el in anchors:
            scene["anchors"][el["id"]] = el
        scene["objects"].append(obj)
        scene["history"].append({"action": "add", "object": obj})
        save_scene(scene)
        # Создаем отношение между объектами
        create_relation(anchor, [obj_parent, obj], "anchor")

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
            "x_0": x1,
            "y_0": y1,
            "width": int(data["width"]),
            "height": height,
            "id": str(short_uuid_base64()),
            "x_rotate": rotate_x,
            "y_rotate": rotate_y,
            "angle": angle * m,
        }

        # Создаем отношение между объектами
        

        # TODO angles on block
        scene["objects"].append(obj)
        anchors = generate_anchors_for_block(obj, no_first=True)
        for el in anchors:
            scene["anchors"][el["id"]] = el
        scene["history"].append({"action": "add", "object": obj})
        save_scene(scene)
        create_relation(nearest_anchor, [obj_parent, obj], "anchor")

    
    return {"status": "relation added"}


@app.post("/add_string")
async def add_string(request: Request):
    data = await request.json()
    scene = load_scene()
    attachment = data["attachment"]

    if attachment == "two-way":
        anchor_1 = scene["anchors"].get(data["anchor_1"])
        anchor_2 = scene["anchors"].get(data["anchor_2"])

        # Находим родительские объекты якорей
        parent_1 = next(
            (obj for obj in scene["objects"] if obj["id"] == anchor_1["parent_id"]),
            None,
        )
        parent_2 = next(
            (obj for obj in scene["objects"] if obj["id"] == anchor_2["parent_id"]),
            None,
        )

        obj = {
            "type": "string",
            "attachment": attachment,
            "id": str(short_uuid_base64()),
            "x1": anchor_1["x"],
            "y1": anchor_1["y"],
            "x2": anchor_2["x"],
            "y2": anchor_2["y"],
        }

        

    elif attachment == "one-way":
        anchor_1 = scene["anchors"].get(data["anchor_1"])
        parent_1 = next(
            (obj for obj in scene["objects"] if obj["id"] == anchor_1["parent_id"]),
            None,
        )

        obj = {
            "type": "string",
            "attachment": attachment,
            "id": str(short_uuid_base64()),
            "x1": anchor_1["x"],
            "y1": anchor_1["y"],
            "x2": data["x"],
            "y2": data["y"],
        }

        # Создаем отношение только в первой точке
        if parent_1:
            create_relation(anchor_1, [parent_1, obj], "string")

    scene["history"].append({"action": "add", "object": obj})
    scene["objects"].append(obj)
    save_scene(scene)
    if parent_1:
        create_relation(anchor_1, [parent_1, obj], "string")

    if attachment == "two-way" and parent_2:
        create_relation(anchor_2, [parent_2, obj], "string")
    
    return {"status": "string added"}


@app.post("/undo")
async def undo(request: Request):
    scene = load_scene()
    if scene["history"]:
        scene["history"].pop()
    if scene["objects"]:
        object = scene["objects"].pop()

        # Удаляем объект из всех отношений
        remove_object_from_relations(scene, object["id"])

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


@app.get("/relations")
async def get_relations(request: Request):
    scene = load_scene()
    return {"relations": scene.get("relations", {})}


@app.get("/relations/{object_id}")
async def get_object_relations(request: Request, object_id: str):
    scene = load_scene()
    relations = find_relations_for_object(scene, object_id)
    return {"object_id": object_id, "relations": relations}


@app.get("/forces")
async def get_forces_analysis(request: Request):
    scene = load_scene()
    analysis = analyze_all_forces(scene)
    return analysis


@app.get("/forces/relation/{relation_id}")
async def get_relation_forces(request: Request, relation_id: str):
    scene = load_scene()
    relation = scene.get("relations", {}).get(relation_id)
    
    if not relation:
        return {"error": "Relation not found"}
    
    analysis = analyze_forces_at_point(relation)
    return analysis


@app.get("/forces/object/{object_id}")
async def get_object_forces(request: Request, object_id: str):
    """Получить все силы, действующие на объект"""
    scene = load_scene()
    analysis = analyze_all_forces(scene)
    
    object_forces = analysis["objects_forces"].get(object_id, [])
    
    if not object_forces:
        return {"error": "Object not found or no forces acting on it"}
    
    return {
        "object_id": object_id,
        "forces": object_forces,
        "force_count": len(object_forces),
        "total_force_magnitude": sum(f["magnitude"] for f in object_forces)
    }
