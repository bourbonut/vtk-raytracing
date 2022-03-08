from collections import namedtuple
import vtk

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


def generate_plane(width, z):
    points = vtk.vtkPoints()
    w = width / 2
    points.InsertNextPoint(-w, z, -w)
    points.InsertNextPoint(w, z, -w)
    points.InsertNextPoint(w, z, w)
    points.InsertNextPoint(-w, z, w)

    # Create the polygon
    polygon = vtk.vtkPolygon()
    polygon.GetPoints().DeepCopy(points)
    polygon.GetPointIds().SetNumberOfIds(4)
    for i in range(4):
        polygon.GetPointIds().SetId(i, i)

    polygons = vtk.vtkCellArray()
    polygons.InsertNextCell(polygon)

    polygonPolyData = vtk.vtkPolyData()
    polygonPolyData.SetPoints(points)
    polygonPolyData.SetPolys(polygons)

    return polygonPolyData, polygon
