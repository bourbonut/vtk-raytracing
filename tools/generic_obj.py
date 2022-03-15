from collections import namedtuple
import vtk
import glm
from math import acos, pi

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


def generate_sphere(phi, theta, center=(0.0, 0.0, 0.0), radius=5.0):
    source = vtk.vtkSphereSource()

    source.SetCenter(*center)
    source.SetRadius(radius)
    source.SetPhiResolution(phi)
    source.SetThetaResolution(theta)
    source.Update()

    return source


def make_obbtree(obj):
    ot = vtk.vtkOBBTree()
    ot.SetDataSet(obj.GetOutput())
    ot.BuildLocator()
    return ot


def generate_plane(width, z, normal=glm.vec3(0, 1, 0), translation=glm.vec3(0, 0, 0)):

    Y = glm.vec3(0, 1, 0)
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

    polygons = vtk.vtkCellArray()
    polygons.InsertNextCell(polygon)

    polygonPolyData = vtk.vtkPolyData()
    polygonPolyData.SetPoints(points)
    polygonPolyData.SetPolys(polygons)

    vtknormals = vtk.vtkDoubleArray()
    vtknormals.SetNumberOfComponents(3)
    vtknormals.SetNumberOfTuples(polygonPolyData.GetNumberOfPoints())

    for i in range(p):
        vtknormals.SetTuple(i, normal)

    # polygonPolyData.GetCellData().SetNormals(vtknormals)
    polygonPolyData.GetPointData().SetNormals(vtknormals)

    obbtree = vtk.vtkOBBTree()
    obbtree.SetDataSet(polygonPolyData)
    obbtree.BuildLocator()

    return polygonPolyData, obbtree


def open_stl(filename):
    reader = vtk.vtkPLYReader()
    reader.SetFileName(filename)
    reader.Update()

    obbtree = make_obbtree(reader)

    return reader, obbtree
