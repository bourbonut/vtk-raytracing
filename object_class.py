from collections import namedtuple

Object = namedtuple(
    "Object",
    [
        "obj",
        "obbtree",
        "color",
        "ambient",
        "diffuse",
        "specular",
        "shininess",
        "reflection",
        "position",
    ],
)
