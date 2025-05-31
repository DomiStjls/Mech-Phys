import os
import json

SCENE_PATH = "data/data.json"
PARAMS_PATH = "data/params.json"


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
        "relations": [],
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
