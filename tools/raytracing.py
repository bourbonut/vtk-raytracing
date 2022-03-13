from math import sqrt, inf, acos
import numpy as np
import glm
import vtk
from vtkmodules.vtkCommonCore import mutable
from time import perf_counter as pf
from rich.progress import Progress
from collections import namedtuple


SimpleObj = namedtuple(
    "SimpleObj",
    [
        "normals",
        "obbtree",
        "ambient",
        "diffuse",
        "specular",
        "shininess",
        "reflection",
        "position",
        "orientation",
    ],
)

Light = namedtuple("Light", ["position", "ambient", "diffuse", "specular"])


def reflected(vector, axis):
    return vector - 2 * glm.dot(vector, axis) * axis


def sphere_intersect(obj, ray_origin, ray_direction):
    p1 = ray_origin
    p2 = ray_origin + 500 * ray_direction

    points = vtk.vtkPoints()
    cellIds = vtk.vtkIdList()

    iD = obj.obbtree.IntersectWithLine(p1, p2, points, cellIds)
    pointData = points.GetData()
    noPoints = pointData.GetNumberOfTuples()
    noIds = cellIds.GetNumberOfIds()

    pointsInter = []
    cellIdsInter = []
    for idx in range(noPoints):
        pointsInter.append(pointData.GetTuple3(idx))
        cellIdsInter.append(cellIds.GetId(idx))

    if iD != 0:
        return glm.length(pointsInter[0] - p1), cellIdsInter[0]
    else:
        return None, None


def nearest_intersected_object(objects, ray_origin, ray_direction):
    distances = [sphere_intersect(obj, ray_origin, ray_direction) for obj in objects]
    nearest_object = None
    min_distance = inf
    subId = -1
    for index, (distance, iD) in enumerate(distances):
        if distance and distance < min_distance:
            min_distance = distance
            nearest_object = objects[index]
            subId = iD
    return nearest_object, min_distance, subId


def get_normals(obj):
    if isinstance(obj.obj, vtk.vtkPolyData):
        return obj.obj.GetCellData().GetNormals()
    else:
        vtknormal = vtk.vtkPolyDataNormals()
        vtknormal.SetInputConnection(obj.obj.GetOutputPort())
        vtknormal.ComputePointNormalsOff()
        vtknormal.ComputeCellNormalsOn()
        vtknormal.SplittingOff()
        vtknormal.FlipNormalsOff()
        vtknormal.AutoOrientNormalsOn()
        vtknormal.Update()
        return vtknormal.GetOutput().GetCellData().GetNormals()


class Data:
    def __init__(self, objects, actors, light, camera):
        self.objects = []
        for obj, actor in zip(objects, actors):
            self.objects.append(
                SimpleObj(
                    get_normals(obj),
                    obj.obbtree,
                    obj.color * obj.ambient,
                    obj.color * obj.diffuse,
                    glm.vec3(1, 1, 1),
                    obj.shininess,
                    obj.reflection,
                    glm.vec3(actor.GetPosition()),
                    glm.vec3(actor.GetOrientation()),
                )
            )
        self.light = Light(
            glm.vec3(light.GetPosition()),
            glm.vec3(1, 1, 1),
            glm.vec3(1, 1, 1),
            glm.vec3(1, 1, 1),
        )
        self.camera = glm.vec3(camera.position)
        self.infos()

    def infos(self):
        print(f"Camera position: {self.camera}")
        print(f"Light position: {self.light.position}")
        for i, obj in enumerate(self.objects):
            print(f"Object {i} position: {obj.position}")


def change_reference(ref):
    Z = glm.vec3(0, 0, 1)
    if glm.length(ref - Z) == 0:
        translation = glm.identity(glm.mat4)
    else:
        translation = glm.translate(ref - Z)

    if glm.length(glm.cross(ref, Z)) == 0:
        rotation = glm.identity(glm.mat4)
    else:
        mag = glm.length(ref)
        angle = acos(glm.dot(Z, ref) / mag) if mag else 0
        axis = glm.cross(Z, ref)
        rotation = glm.rotate(angle, axis)

    return rotation, translation


def generate_image(objects, actors, light, camera, max_depth=3, width=300, height=200):
    # Parameters
    data = Data(objects, actors, light, camera)
    ratio = width / height
    screen = (-1, 1 / ratio, 1, -1 / ratio)

    matrix_rot, matrix_trans = change_reference(glm.normalize(data.camera))

    zoom = 20

    # Initialization of the image
    image = np.zeros((height, width, 3))
    with Progress(auto_refresh=False) as progress:
        task = progress.add_task("Generating ...", total=height)
        for i, y in enumerate(np.linspace(screen[1], screen[3], height)):
            for j, x in enumerate(np.linspace(screen[0], screen[2], width)):
                # screen is on origin
                pixel = matrix_rot * glm.vec3(x, y, 0) * zoom
                origin = matrix_trans * data.camera * zoom
                direction = glm.normalize(pixel - origin)

                color = glm.vec3()
                reflection = 1

                for k in range(max_depth):
                    # check for intersections
                    nearest_object, min_distance, subId = nearest_intersected_object(
                        data.objects, origin, direction
                    )
                    if nearest_object is None:
                        break

                    intersection = origin + min_distance * direction
                    normal_to_surface = glm.normalize(nearest_object.normals.GetTuple(subId))
                    shifted_point = intersection + 1e-5 * normal_to_surface
                    intersection_to_light = glm.normalize(data.light.position - shifted_point)

                    _, min_distance, _ = nearest_intersected_object(
                        data.objects, shifted_point, intersection_to_light
                    )
                    intersection_to_light_distance = glm.length(
                        data.light.position - intersection
                    )
                    is_shadowed = min_distance < intersection_to_light_distance

                    if is_shadowed:
                        break

                    illumination = glm.vec3()

                    # ambiant
                    illumination += nearest_object.ambient * data.light.ambient

                    # diffuse
                    illumination += (
                        nearest_object.diffuse
                        * data.light.diffuse
                        * glm.dot(intersection_to_light, normal_to_surface)
                    )

                    # specular
                    intersection_to_camera = glm.normalize(data.camera - intersection)
                    H = glm.normalize(intersection_to_light + intersection_to_camera)
                    illumination += (
                        nearest_object.specular
                        * data.light.specular
                        * glm.dot(normal_to_surface, H) ** (nearest_object.shininess / 4)
                    )

                    # reflection
                    color += reflection * illumination
                    reflection *= nearest_object.reflection

                    origin = shifted_point
                    direction = reflected(direction, normal_to_surface)

                image[i, j] = np.clip(color, 0, 1)
            # print("%d/%d" % (i + 1, height))
            progress.advance(task)
            progress.refresh()
    return image
