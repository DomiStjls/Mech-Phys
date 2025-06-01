import os
import json
import uuid
import base64

SCENE_PATH = "data/data.json"
PARAMS_PATH = "data/params.json"

def short_uuid_base64():
    u = uuid.uuid4()
    return base64.urlsafe_b64encode(u.bytes).rstrip(b"=").decode("ascii")

def get_default_params():
    return {
        "plane_angle": 0,
        "plane_length": 500,
        "block_width": 80,
        "block_height": 40,
        "string_attachment": "one-way",
    }


def load_scene(clear=False):
    if os.path.exists(SCENE_PATH) and not clear:
        with open(SCENE_PATH, "r") as f:
            return json.load(f)
    return {
        "objects": [],
        "relations": {},
        "history": [],
        "anchors": {},
        "mode": "plane",
        "params": get_default_params(),
        # "svg_objects": [],
    }


def load_params():
    if os.path.exists(PARAMS_PATH):
        with open(PARAMS_PATH, "r") as f:
            return json.load(f)
    return get_default_params()


def save_params(params):
    os.makedirs(os.path.dirname(PARAMS_PATH), exist_ok=True)
    with open(PARAMS_PATH, "w") as f:
        json.dump(params, f, indent=2)


def save_scene(scene):
    os.makedirs(os.path.dirname(SCENE_PATH), exist_ok=True)
    with open(SCENE_PATH, "w") as f:
        json.dump(scene, f)


def create_relation(anchor=None, objects=None, relation_type="anchor"):
    """
    scene: словарь сцены
    anchor_point: точка (dict с x, y координатами)
    objects: список объектов для связи
    relation_type: тип отношения ("anchor", "string")
    """
    scene = load_scene()
    if anchor:

        existing_relation_id = None
        for rel_id, relation in scene["relations"].items():
            if relation["anchor_id"] == anchor['id']:
                existing_relation_id = rel_id
                break
        if existing_relation_id:
            if objects:
                for obj in objects:
                    if (
                        obj["id"]
                        not in scene["relations"][existing_relation_id]["object_ids"]
                    ):
                        scene["relations"][existing_relation_id]["object_ids"].append(
                            obj["id"]
                        )
            save_scene(scene)
            return existing_relation_id
        else:
            # Создаем новое отношение
            relation_id = str(short_uuid_base64())
            scene["relations"][relation_id] = {
                "id": relation_id,
                "type": relation_type,
                "anchor_id": anchor['id'],
                "x": anchor["x"],
                "y": anchor["y"],
                "object_ids": [obj["id"] for obj in objects] if objects else [],
            }
            save_scene(scene)
            print(relation_id)
            return relation_id
    
    return None


def find_relations_for_object(scene, object_id):
    """Находит все отношения для объекта"""
    relations = []
    for rel_id, relation in scene.get("relations", {}).items():
        if object_id in relation["object_ids"]:
            relations.append(relation)
    return relations


def remove_object_from_relations(scene, object_id):
    """Удаляет объект из всех отношений"""
    relations_to_remove = []

    for rel_id, relation in scene.get("relations", {}).items():
        if object_id in relation["object_ids"]:
            relation["object_ids"].remove(object_id)
            # Если в отношении остался только один объект или меньше, удаляем отношение
            if len(relation["object_ids"]) <= 1:
                relations_to_remove.append(rel_id)

    # Удаляем пустые отношения
    for rel_id in relations_to_remove:
        del scene["relations"][rel_id]
    save_scene(scene)

