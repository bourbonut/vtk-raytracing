from collections import namedtuple
from itertools import starmap, repeat
from math import acos

import vtk
import glm

PLANE_NORMALS = [
    glm.vec3(0, 1, 0),
    glm.vec3(0, 0, 1),
    glm.vec3(1, 0, 0),
    glm.vec3(0, -1, 0),
    glm.vec3(0, 0, -1),
    glm.vec3(-1, 0, 0),
]

PLANE_TRANSLATIONS = [
    glm.vec3(0, 0, 0),
    glm.vec3(0, -30, -30),
    glm.vec3(-30, -30, 0),
    glm.vec3(0, 100, 0),
    glm.vec3(0, -30, 30),
    glm.vec3(30, -30, 0),
]


Object = namedtuple("Object", ["item", "obbtree", "material", "position"])


def _generate_obbtree(obj, getoutput):
    """
    Return a `vtkObbtree` given the object
    For convenience, `getoutput` is used depending of the input `obj`
    """
    ot = vtk.vtkOBBTree()
    ot.SetDataSet(obj.GetOutput() if getoutput else obj)
    ot.BuildLocator()
    return ot


def _generate_sphere(phi, theta, center, radius):
    """
    Return a `vtkSphere` given the arguments
    """
    source = vtk.vtkSphereSource()

    source.SetCenter(*center)
    source.SetRadius(radius)
    source.SetPhiResolution(phi)
    source.SetThetaResolution(theta)
    source.Update()

    return source


def _generate_obj_ply(filename):
    """
    Return a object which can be manipulate with VTK
    """
    reader = vtk.vtkPLYReader()
    reader.SetFileName(filename)
    reader.Update()
    return reader


def _generate_plane(width, z, normal, translation):
    """
    Return a plane given the arguments
    """
    Y = glm.vec3(0, 1, 0)  # reference
    if glm.length(glm.cross(normal, Y)) == 0:
        rotation = glm.identity(glm.mat4)
    elif glm.length(normal + Y) == 0:
        rotation = glm.rotate(pi)
    else:
        mag = glm.length(normal)
        angle = acos(glm.dot(Y, normal) / mag) if mag else 0
        axis = glm.cross(Y, normal)
        rotation = glm.rotate(angle, axis)

    rotation *= glm.translate(translation)

    # Generate points of the plane
    points = vtk.vtkPoints()
    w = width / 2
    p = 4
    points.InsertNextPoint(rotation * glm.vec3(-w, z, -w))
    points.InsertNextPoint(rotation * glm.vec3(w, z, -w))
    points.InsertNextPoint(rotation * glm.vec3(w, z, w))
    points.InsertNextPoint(rotation * glm.vec3(-w, z, w))

    # Create the polygon
    polygon = vtk.vtkPolygon()
    polygon.GetPoints().DeepCopy(points)
    polygon.GetPointIds().SetNumberOfIds(p)
    for i in range(p):
        polygon.GetPointIds().SetId(i, i)

    # Generate cells
    polygons = vtk.vtkCellArray()
    polygons.InsertNextCell(polygon)

    # Generate data
    polygonPolyData = vtk.vtkPolyData()
    polygonPolyData.SetPoints(points)
    polygonPolyData.SetPolys(polygons)

    # Generate normals
    vtknormals = vtk.vtkDoubleArray()
    vtknormals.SetNumberOfComponents(3)
    vtknormals.SetNumberOfTuples(polygonPolyData.GetNumberOfPoints())
    for i in range(p):
        vtknormals.SetTuple(i, -normal)
    polygonPolyData.GetPointData().SetNormals(vtknormals)

    return polygonPolyData


def _generate_actor(mapper, material, position):
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(material[0])
    actor.GetProperty().SetAmbient(material[1])
    actor.GetProperty().SetDiffuse(material[2])
    actor.GetProperty().SetSpecular(material[3])
    actor.SetPosition(position)
    return actor


def generate_data(objects, labels=None):
    """
    Return the processed objects, processed labels and actors
    """
    convert2vec3 = lambda data: glm.vec3(*data) if isinstance(data, list) else data
    processed_objects = []
    actors = []

    for description in objects:
        objtype, arguments = description["item"]
        material = [convert2vec3(data) for data in description["material"]]
        position = description["position"]
        if objtype == "sphere":
            mapper = vtk.vtkPolyDataMapper()
            obj = _generate_sphere(*arguments)
            obbtree = _generate_obbtree(obj, True)
            result = Object(obj, obbtree, material, position)
            processed_objects.append(result)
            mapper.SetInputConnection(obj.GetOutputPort())
            actors.append(_generate_actor(mapper, material, position))
        elif objtype == "ply":
            mapper = vtk.vtkPolyDataMapper()
            obj = _generate_obj_ply(arguments)
            obbtree = _generate_obbtree(obj, True)
            result = Object(obj, obbtree, material, position)
            processed_objects.append(result)
            mapper.SetInputConnection(obj.GetOutputPort())
            actors.append(_generate_actor(mapper, material, position))
        elif objtype == "planes":
            normals = [PLANE_NORMALS[i] for i in arguments]
            translations = [PLANE_TRANSLATIONS[i] for i in arguments]
            params = zip(repeat(100), repeat(-20), normals, translations)
            objs = list(starmap(_generate_plane, params))
            obbtrees = [_generate_obbtree(obj, False) for obj in objs]
            result = [Object(obj, ot, material, position) for obj, ot in zip(objs, obbtrees)]
            processed_objects.extend(result)
            for obj in objs:
                mapper = vtk.vtkPolyDataMapper()
                mapper.SetInputData(obj)
                # mapper.SetInputConnection(obj.GetOutputPort())
                actors.append(_generate_actor(mapper, material, position))
        else:
            raise Exception(f'"{objtype}" type not implemented')

    if labels and "$PLANES" in labels:
        index = labels.index("$PLANES")
        length_planes = len(processed_objects) - len(labels) + 1
        planes_labels = [f"Plane {i}" for i in range(length_planes)]
        processed_labels = labels[:index] + planes_labels + labels[index + 1 :]
    else:
        processed_labels = [f"Object {i}" for i in range(processed_objects)]

    return processed_objects, processed_labels, actors
