from math import sqrt, inf
import glm
import vtk
from vtkmodules.vtkCommonCore import mutable
from time import perf_counter as pf


def reflected(vector, axis):
    return vector - 2 * glm.dot(vector, axis) * axis


def sphere_intersect(obj, ray_origin, ray_direction):
    p1 = ray_origin
    p2 = ray_origin + 10 * ray_direction
    M = obj.position
    # while glm.length2(p2 - p1) < 2 * glm.length2(M - p1):
    #     p2 += ray_direction

    tolerance = 0.001
    t = mutable(0)
    x = [0.0, 0.0, 0.0]
    pcoords = [0.0, 0.0, 0.0]
    subId = mutable(0)
    iD = obj.obbtree.IntersectWithLine(p1, p2, tolerance, t, x, pcoords, subId)
    if iD == 1:
        return glm.length(x - p1)
    else:
        return None


# def sphere_intersect(center, radius, ray_origin, ray_direction):
#     b = 2 * glm.dot(ray_direction, ray_origin - center)
#     c = glm.length2(ray_origin - center) - radius * radius
#     delta = b * b - 4 * c
#     if delta > 0:
#         t1 = (-b + sqrt(delta)) / 2
#         t2 = (-b - sqrt(delta)) / 2
#         if t1 > 0 and t2 > 0:
#             return min(t1, t2)
#     return None


def nearest_intersected_object(objects, ray_origin, ray_direction):
    distances = [sphere_intersect(obj, ray_origin, ray_direction) for obj in objects]
    nearest_object = None
    min_distance = inf
    for index, distance in enumerate(distances):
        if distance and distance < min_distance:
            min_distance = distance
            nearest_object = objects[index]
    return nearest_object, min_distance
