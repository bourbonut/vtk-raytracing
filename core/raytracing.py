from .utils import *
import glm, vtk, numpy as np
from math import inf, acos
from vtkmodules.vtkCommonCore import mutable
from rich.progress import Progress


def find_intersection(obbtree, ray_origin, ray_direction):
    """
    Return:
    - the distance between the initial point and the intersection
    - the id of intersected cell
    - the coordinates of intersected point
    """
    p1 = ray_origin
    p2 = ray_origin + 500 * ray_direction

    points = vtk.vtkPoints()
    cellIds = vtk.vtkIdList()

    iD = obbtree.IntersectWithLine(p1, p2, points, cellIds)
    pointData = points.GetData()
    noPoints = pointData.GetNumberOfTuples()
    noIds = cellIds.GetNumberOfIds()

    pointsInter = []
    cellIdsInter = []
    for idx in range(noPoints):
        pointsInter.append(pointData.GetTuple3(idx))
        cellIdsInter.append(cellIds.GetId(idx))

    if iD != 0:
        return glm.length(pointsInter[0] - p1), cellIdsInter[0], pointsInter[0]
    else:
        return None, None, None


def nearest_intersected_object(objects, ray_origin, ray_direction):
    """
    Return the nearest intersected object
    """
    nearest_object, min_distance, subId, target = None, inf, -1, []
    for obj in objects:
        distance, iD, x = find_intersection(obj.data.obbtree, ray_origin, ray_direction)
        if distance and distance < min_distance:
            min_distance = distance
            nearest_object = obj
            subId = iD
            target = x
    return nearest_object, min_distance, subId, target


def contribute(material, light, i2c, i2l, n2s):
    """
    Return the contribution value
    """
    illumination = glm.vec3()
    # ambiant
    illumination += material.ambient * light.ambient
    # diffuse
    illumination += material.diffuse * light.diffuse * glm.dot(i2l, n2s)
    # specular
    k = glm.dot(n2s, glm.normalize(i2l + i2c)) ** (material.shininess * 0.25)
    illumination += material.specular * light.specular * k
    return illumination


def generate_image(scene, max_depth=3, width=300, height=200, zoom=20):
    """
    Apply an array where raytracing was applied on the scene
    """
    # Parameters
    ratio = width / height
    screen = (-1, 1 / ratio, 1, -1 / ratio)

    matrix_rot, matrix_trans = change_reference(glm.normalize(scene.camera))
    # Initialization of the image
    image = np.zeros((height, width, 3))
    with Progress(auto_refresh=False) as progress:
        task = progress.add_task("Generating ...", total=height)
        for i, y in enumerate(np.linspace(screen[1], screen[3], height)):
            for j, x in enumerate(np.linspace(screen[0], screen[2], width)):
                # screen is on origin
                pixel = matrix_rot * glm.vec3(x, y, 0) * zoom
                origin = matrix_trans * scene.camera * zoom
                direction = glm.normalize(pixel - origin)

                color = glm.vec3()
                reflection = 1

                for _ in range(max_depth):
                    # Check for intersections
                    result = nearest_intersected_object(scene.objects, origin, direction)
                    nearest_object, min_distance, subId, target = result
                    if nearest_object is None:
                        break

                    # Exctract informations
                    polydata = nearest_object.data.polydata
                    normals = nearest_object.data.normals
                    material = nearest_object.material
                    intersection = origin + min_distance * direction
                    points = [polydata.GetCell(subId).GetPoints().GetPoint(i) for i in range(3)]
                    ids = [polydata.GetCell(subId).GetPointIds().GetId(i) for i in range(3)]
                    normals = [normals.GetTuple(id_) for id_ in ids]

                    # Compute normal and intersection
                    # n2s = normal to surface
                    # i2l = intersection to light
                    # i2c = intersection to camera
                    n2s = glm.normalize(interpolation(points, normals, target))
                    shifted_point = intersection + 1e-5 * n2s
                    i2l = glm.normalize(scene.light.position - shifted_point)

                    # Check if shadowed
                    result = nearest_intersected_object(scene.objects, shifted_point, i2l)
                    i2l_distance = glm.length(scene.light.position - intersection)
                    if result[1] < i2l_distance:  # is shadowed
                        break

                    # Contribution
                    i2c = glm.normalize(scene.camera - intersection)
                    illumination = contribute(material, scene.light, i2c, i2l, n2s)

                    # Reflection
                    color += reflection * illumination
                    reflection *= material.reflection

                    # New initial coordinates
                    origin = shifted_point
                    direction = reflected(direction, n2s)

                image[i, j] = np.clip(color, 0, 1)

            progress.advance(task)
            progress.refresh()
    return image
