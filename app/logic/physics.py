import math

from app.logic.features import load_scene

g = 10
ro = 0.01
p = 0.01
def analyze_forces_at_point(relation):
    """
    Анализирует силы, действующие в точке отношения

    Args:
        scene: словарь сцены
        relation: отношение для анализа

    Returns:
        dict: анализ сил в точке
    """
    forces = []
    scene = load_scene()
    point_x, point_y = relation["x"], relation["y"]
    objects_in_relation = []
    for obj_id in relation["object_ids"]:
        obj = next((o for o in scene["objects"] if o["id"] == obj_id), None)
        if obj:
            objects_in_relation.append(obj)

    for obj in objects_in_relation:
        if obj["type"] == "block":
            mass = obj.get(
                "mass", obj["width"] * obj["height"] * ro
            )  # заглушка на массу надо бы добавить это в форму
            gravity_force = {
                "type": "gravity",
                "name": "F_g",
                "magnitude": mass * g,  # mg
                "angle": 270,  # вниз всегда
                "direction": "down",
                "object_id": obj["id"],
                "description": f"Сила тяжести блока (масса ≈ {mass:.2f} кг)",
            }
            forces.append(gravity_force)
            # Проверяем, лежит ли блок на плоскости
            plane_supports = [
                o
                for o in objects_in_relation
                if o["type"] == "plane" and o["id"] != obj["id"]
            ]
            for plane in plane_supports:
                # Сила реакции опоры (перпендикулярно плоскости)
                plane_angle = plane["angle"]
                normal_angle = (plane_angle + 90) % 360

                normal_force = {
                    "type": "normal",
                    "name": "N",
                    "magnitude": mass * g * math.cos(math.radians(plane_angle)),
                    "angle": normal_angle,
                    "direction": "perpendicular_to_plane",
                    "object_id": obj["id"],
                    "plane_id": plane["id"],
                    "description": f"Сила реакции опоры от плоскости (угол {plane_angle}°)",
                }
                forces.append(normal_force)

                # Сила трения (вдоль плоскости, противоположно возможному движению)
                friction_angle = (plane_angle + 180) % 360
                friction_coefficient = 0.3  # условный коэффициент трения

                friction_force = {
                    "type": "friction",
                    "name": "F_tr",
                    "magnitude": friction_coefficient * normal_force["magnitude"],
                    "angle": friction_angle,
                    "direction": "along_plane_opposite",
                    "object_id": obj["id"],
                    "plane_id": plane["id"],
                    "description": f"Сила трения (μ = {friction_coefficient})",
                }
                forces.append(friction_force)

        elif obj["type"] == "string":
            # Для нити - сила натяжения
            string_angle = math.degrees(
                math.atan2(obj["y2"] - obj["y1"], obj["x2"] - obj["x1"])
            )

            # Находим подвешенные объекты
            suspended_objects = [
                o
                for o in objects_in_relation
                if o["type"] == "block" and o["id"] != obj["id"]
            ]

            total_tension = 0
            for suspended_obj in suspended_objects:
                mass = suspended_obj.get(
                    "mass", suspended_obj["width"] * suspended_obj["height"] * ro
                )
                total_tension += mass * g

            if total_tension > 0:
                tension_force = {
                    "type": "tension",
                    "name": "T",
                    "magnitude": total_tension,
                    "angle": string_angle,
                    "direction": "along_string",
                    "object_id": obj["id"],
                    "description": f"Сила натяжения нити (угол {string_angle:.1f}°)",
                }
                forces.append(tension_force)

        elif obj["type"] == "plane":
            # Плоскость может передавать силы реакции опоры
            supported_objects = [
                o
                for o in objects_in_relation
                if o["type"] == "block" and o["id"] != obj["id"]
            ]

            for supported_obj in supported_objects:
                mass = supported_obj.get(
                    "mass", supported_obj["width"] * supported_obj["height"] * ro
                )
                plane_angle = obj["angle"]

                # Реакция на плоскость (противоположна нормальной силе)
                reaction_angle = (plane_angle - 90) % 360

                reaction_force = {
                    "type": "reaction",
                    "name": "R",
                    "magnitude": mass * g * math.cos(math.radians(plane_angle)),
                    "angle": reaction_angle,
                    "direction": "into_plane",
                    "object_id": obj["id"],
                    "from_object_id": supported_obj["id"],
                    "description": f"Реакция плоскости на давление блока",
                }
                forces.append(reaction_force)

    return {
        "point": {"x": point_x, "y": point_y},
        "relation_id": relation["id"],
        "forces": forces,
        "force_count": len(forces),
        "equilibrium_check": check_equilibrium(forces),
    }


def check_equilibrium(forces):
    """Проверяет равновесие сил в точке"""
    sum_x = sum(f["magnitude"] * math.cos(math.radians(f["angle"])) for f in forces)
    sum_y = sum(f["magnitude"] * math.sin(math.radians(f["angle"])) for f in forces)

    total_magnitude = math.sqrt(sum_x**2 + sum_y**2)

    return {
        "is_equilibrium": total_magnitude < 0.1,  # допуск
        "resultant_magnitude": total_magnitude,
        "resultant_angle": math.degrees(math.atan2(sum_y, sum_x))
        if total_magnitude > p
        else 0,
        "sum_x": sum_x,
        "sum_y": sum_y,
    }


def analyze_all_forces(scene):
    """
    Анализирует все силы во всех точках отношений

    Args:
        scene: словарь сцены

    Returns:
        dict: полный анализ сил в системе
    """
    analysis = {
        "relations_analysis": [],
        "objects_forces": {},
        "system_summary": {
            "total_relations": 0,
            "total_forces": 0,
            "equilibrium_points": 0,
        },
    }

    relations = scene.get("relations", {})

    for relation_id, relation in relations.items():
        force_analysis = analyze_forces_at_point(relation)
        analysis["relations_analysis"].append(force_analysis)

        # Собираем силы по объектам
        for force in force_analysis["forces"]:
            obj_id = force["object_id"]
            if obj_id not in analysis["objects_forces"]:
                analysis["objects_forces"][obj_id] = []
            analysis["objects_forces"][obj_id].append(force)

        # Обновляем статистику
        analysis["system_summary"]["total_forces"] += len(force_analysis["forces"])
        if force_analysis["equilibrium_check"]["is_equilibrium"]:
            analysis["system_summary"]["equilibrium_points"] += 1

    analysis["system_summary"]["total_relations"] = len(relations)

    return analysis
