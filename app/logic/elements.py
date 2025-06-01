import math

from app.logic.features import load_scene


def find_nearest_anchor(x, y, anchors, tolerance=5):
    for anchor in anchors:
        dx = anchor["x"] - x
        dy = anchor["y"] - y
        if abs(dx) <= tolerance and abs(dy) <= tolerance:
            return anchor
    return None


def create_anchor_svg(anchor):
    x = anchor["x"]
    y = anchor["y"]
    color = "blue" if anchor["parent_type"] == "plane" else "green"
    return f'<circle class="anchor-point" data-id="{anchor["id"]}" cx="{x}" cy="{y}" r="5" fill="{color}" stroke="black" />'


def creat_anchor(x, y, parent_id, id, parent_type):
    # проверка на то что точка с такими координатами существует
    anchors = load_scene()["anchors"].values()
    if find_nearest_anchor(x, y, anchors, tolerance=1) is not None:
        return None
    return {
        "id": f"{id}",
        "type": "anchor",
        "x": x,
        "y": y,
        "parent_id": parent_id,
        "parent_type": parent_type,
    }


def generate_anchors_for_plane(obj, spacing=40, no_first=False):
    anchors = []
    x_start = obj["x_0"]
    y_start = obj["y_0"]
    angle = obj.get("angle", 0)
    length = obj.get("length", 500)
    new_step = length / 2
    while new_step > spacing * 2:
        new_step /= 2
    num_anchors = length // new_step + 1
    print(new_step, num_anchors)
    for i in range(int(no_first), int(num_anchors)):
        x = round(x_start + i * new_step * math.cos(math.radians(angle)), 2)
        y = round(y_start - i * new_step * math.sin(math.radians(angle)), 2)
        anchor = creat_anchor(x, y, obj["id"], f"{obj['id']}_{i}", obj["type"])
        anchors.append(anchor)
    return anchors


def generate_anchors_for_block(block, step=40, no_first=False):
    x, y = block["x_0"], block["y_0"]
    width = int(block.get("width", 80))
    height = int(block.get("height", 40))
    anchors = []
    new_step = width
    k = 0
    angle = abs(block.get("angle", 0))
    cos = math.cos(math.radians(angle))
    sin = math.sin(math.radians(angle))

    for i in range(5):
        if (not no_first and i == 0) or i != 0:
            anchor = creat_anchor(
                round(x + i / 4 * new_step * cos, 2),
                round(y - i / 4 * new_step * sin, 2),
                block["id"],
                f"{block['id']}_{k}",
                block["type"],
            )
            k += 1
            print(anchor)
            if anchor is not None:
                anchors.append(anchor)
        anchor = creat_anchor(
            round(x + i / 4 * new_step * cos - height * sin, 2),
            round(y - height * cos - i / 4 * new_step * sin, 2),
            block["id"],
            f"{block['id']}_{k}",
            block["type"],
        )
        k += 1
        if anchor is not None:
            anchors.append(anchor)

    new_step = height / 2
    anchor = creat_anchor(
        round(x - new_step * sin, 2),
        round(y - new_step * cos, 2),
        block["id"],
        f"{block['id']}_{k}",
        block["type"],
    )
    if anchor is not None:
        anchors.append(anchor)
    k += 1
    anchor = creat_anchor(
        round(x + width * cos - new_step * sin, 2),
        round(y - new_step * cos - width * sin, 2),
        block["id"],
        f"{block['id']}_{k}",
        block["type"],
    )

    if anchor is not None:
        anchors.append(anchor)
    k += 1
    return anchors


def create_plane_svg(obj):
    """
    "type": "plane",
    "x_center": x,
    "y_center": y,
    "length": length,
    "angle": angle,
    "id": str(uuid.uuid4()),
    "x_0": int(x - 0.5 * int(data["length"]) * math.cos(math.radians(angle))),
    "y_0": int(y + 0.5 * int(data["length"]) * math.sin(math.radians(angle))),
    """
    x1 = obj["x_0"]
    y1 = obj["y_0"]
    angle = obj.get("angle", 0)
    length = int(obj.get("length", 500))
    x2 = x1 + length * math.cos(math.radians(angle))
    y2 = y1 - length * math.sin(math.radians(angle))
    svg = f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="black" stroke-width="6" data-id="{obj["id"]}" />'
    return svg


def create_block_svg(obj):
    """
    "type": "block",
    "x_center": x,
    "y_center": y,
    "width": width,
    "height": height,
    "id": str(uuid.uuid4()),
    "x_0": int(x - 0.5 * width),
    "y_0": int(y - 0.5 * height),
    "x_rotate": ,
    "y_rotate": ,
    "angle": 0,
    """
    # x = obj["x_0"]
    # y = obj["y_0"]

    width = int(obj.get("width", 80))
    height = int(obj.get("height", 40))
    x_rotate = obj["x_rotate"]
    y_rotate = obj["y_rotate"]
    svg = f'<rect x="{x_rotate}" y="{y_rotate}" width="{width}" height="{height}" fill="green" fill-opacity="0.4" stroke="black" transform="rotate({obj["angle"]}, {x_rotate}, {y_rotate})" />'
    return svg


def create_string_svg(obj):
    """
    "type": "string",
    "attachment": attachment,
    "id": str(uuid.uuid4()),
    "x1": x,
    "x2": x,
    "y1": y,
    "y2": y,
    """
    x = obj["x1"]
    y = obj["y1"]
    x2 = obj.get("x2", x + 100)
    y2 = obj.get("y2", y)
    if obj["attachment"] == "two-way":
        svg = f'<line x1="{x}" y1="{y}" x2="{x2}" y2="{y2}" stroke="black" stroke-width="2" />'
    else:
        angle = math.atan2(y2 - y, x2 - x)
        xp1 = x2 - 20 * math.sin(angle)
        yp1 = y2 + 20 * math.cos(angle)
        xp2 = x2 + 20 * math.sin(angle)
        yp2 = y2 - 20 * math.cos(angle)
        svg = (
            f'<line x1="{x}" y1="{y}" x2="{x2}" y2="{y2}" stroke="black" stroke-width="2" />\n'
            + f'<line x1="{xp1}" y1="{yp1}" x2="{xp2}" y2="{yp2}" stroke="black" stroke-width="5" />'
        )
    return svg


def generate_svg_for_object(obj):
    
    if obj["type"] == "plane":
        return create_plane_svg(obj)
    elif obj["type"] == "block":
        return create_block_svg(obj)
    elif obj["type"] == "string":
        return create_string_svg(obj)
    elif obj["type"] == "anchor":
        return create_anchor_svg(obj)
    return None
