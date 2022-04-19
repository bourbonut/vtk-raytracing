import json
from itertools import starmap

SCENE = ["width", "height", "zoom", "max_depth"]
ITEMS = {
    "sphere": ["theta", "phi", "center", "radius"],
    "plane": ["height translation"],
    "planes": "indexes",
    "ply": "path",
}
MATERIAL = ["color", "ambient", "diffuse", "specular", "shininess", "reflection"]
LIGHT = ["position", "cone angle"]


def describe(filename):
    with open(f"./configurations/{filename}", "r") as f:
        config = json.load(f)
    formatter = lambda a, b: str(a) + ": " + str(b)
    msg = []
    for spec in config:
        lvl1 = config[spec]
        if spec == "scene":
            string = "Scene:{" + ", ".join(starmap(formatter, zip(SCENE, lvl1))) + "}"
            msg.append(string)
        elif spec == "objects":
            msg.append("Objects{")
            for i, obj in enumerate(lvl1):
                msg.append(" " * 4 + "Object_" + str(i) + "{")
                for section in obj:
                    lvl2 = obj[section]
                    if section == "item":
                        t = lvl2[0]  # type
                        string = " " * 8 + str(t) + "<"
                        string += ", ".join(starmap(formatter, zip(ITEMS[t], lvl2[1]))) + ">"
                        msg.append(string)
                    elif section == "material":
                        string = " " * 8 + section
                        string += "<" + ", ".join(starmap(formatter, zip(MATERIAL, lvl2))) + ">"
                        msg.append(string)
                    elif section == "position":
                        msg.append(" " * 8 + section + " : " + str(lvl2))
                    else:
                        msg.append(" " * 8 + section + " not implemented")
                msg.append(" " * 4 + "}")
            msg.append("}")
        elif spec == "light":
            string = "Light:{" + ", ".join(starmap(formatter, zip(LIGHT, lvl1))) + "}"
            msg.append(string)
        elif spec == "target":
            msg.append("Selected object, where light focuses on, is " + str(lvl1))
        elif spec == "camera":
            msg.append("Camera:{position : " + str(lvl1) + "}")
        elif spec == "name":
            msg.append("Name of the simulation : " + lvl1)
    return msg
