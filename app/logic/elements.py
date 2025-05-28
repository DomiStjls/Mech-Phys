import math


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
    while new_step > step * 2:
        anchor = creat_anchor(
            round(x + new_step * cos, 2),
            round(y - new_step * sin, 2),
            block["id"],
            f"{block['id']}_{k}",
            block["type"],
        )
        k += 1
        anchors.append(anchor)
        anchor = creat_anchor(
            round(x + new_step * cos - height * sin, 2),
            round(y - height * cos - new_step * sin, 2),
            block["id"],
            f"{block['id']}_{k}",
            block["type"],
        )
        k += 1
        anchors.append(anchor)
        new_step /= 2

    # print(new_step, num_anchors, block["angle"])
    # for i in range(int(no_first), int(num_anchors) - 1):
    #     anchor = creat_anchor(
    #         round(x + i * new_step * cos, 2),
    #         round(y - i * new_step * sin, 2),
    #         block["id"],
    #         f"{block['id']}_{k}",
    #         block["type"],
    #     )
    #     k += 1
    #     anchors.append(anchor)
    #     anchor = creat_anchor(
    #         round(x + i * new_step * cos - height * sin, 2),
    #         round(y - height * cos - i * new_step * sin, 2),
    #         block["id"],
    #         f"{block['id']}_{k}",
    #         block["type"],
    #     )
    #     k += 1
    #     anchors.append(anchor)

    new_step = height
    while new_step > step:
        anchor = creat_anchor(
            round(x - new_step * sin, 2),
            round(y - new_step * cos, 2),
            block["id"],
            f"{block['id']}_{k}",
            block["type"],
        )
        anchors.append(anchor)
        k += 1
        anchor = creat_anchor(
            round(x + width * cos - new_step * sin, 2),
            round(y - new_step * cos - width * sin, 2),
            block["id"],
            f"{block['id']}_{k}",
            block["type"],
        )
        anchors.append(anchor)
        k += 1
        new_step /= 2
    num_anchors = height / new_step + 1
    print(new_step, num_anchors)
    # for i in range(1, int(num_anchors) - 1):
    #     anchor = creat_anchor(
    #         round(x - new_step * sin, 2),
    #         round(y - i * new_step * cos, 2),
    #         block["id"],
    #         f"{block['id']}_{k}",
    #         block["type"],
    #     )
    #     anchors.append(anchor)
    #     k += 1
    #     anchor = creat_anchor(
    #         round(x + width * cos - new_step * sin, 2),
    #         round(y - i * new_step * cos - width * sin, 2),
    #         block["id"],
    #         f"{block['id']}_{k}",
    #         block["type"],
    #     )
    #     anchors.append(anchor)
    #     k += 1
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
    "x_0": x,
    "y_0": y,
    "angle": 0,
    """
    x = obj["x_0"]
    y = obj["y_0"]
    x2 = obj.get("x2", x + 100)
    y2 = obj.get("y2", y)
    svg = f'<line x1="{x}" y1="{y}" x2="{x2}" y2="{y2}" stroke="black" stroke-width="2" />'
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
