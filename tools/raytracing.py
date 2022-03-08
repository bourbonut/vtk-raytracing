from math import sqrt, inf
import numpy as np
import glm
import vtk
from vtkmodules.vtkCommonCore import mutable
from time import perf_counter as pf
from rich.progress import Progress


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
    # st = pf()
    iD = obj.obbtree.IntersectWithLine(p1, p2, tolerance, t, x, pcoords, subId)
    # duration = pf() - st
    # print(duration)
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


def generate_image(objects, light, camera, max_depth=3, width=300, height=200):
    # Parameters
    ratio = width / height
    screen = (-1, 1 / ratio, 1, -1 / ratio)

    # Initialization of the image
    image = np.zeros((height, width, 3))
    with Progress(auto_refresh=False) as progress:
        task = progress.add_task("Generating ...", total=height)
        for i, y in enumerate(np.linspace(screen[1], screen[3], height)):
            for j, x in enumerate(np.linspace(screen[0], screen[2], width)):
                # screen is on origin
                pixel = glm.vec3(x, y, 0)
                origin = camera
                direction = glm.normalize(pixel - origin)

                color = glm.vec3()
                reflection = 1

                for k in range(max_depth):
                    # check for intersections
                    nearest_object, min_distance = nearest_intersected_object(
                        objects, origin, direction
                    )
                    if nearest_object is None:
                        break

                    intersection = origin + min_distance * direction
                    normal_to_surface = glm.normalize(intersection - nearest_object.position)
                    shifted_point = intersection + 1e-5 * normal_to_surface
                    intersection_to_light = glm.normalize(light["position"] - shifted_point)

                    _, min_distance = nearest_intersected_object(
                        objects, shifted_point, intersection_to_light
                    )
                    intersection_to_light_distance = glm.length(
                        light["position"] - intersection
                    )
                    is_shadowed = min_distance < intersection_to_light_distance

                    if is_shadowed:
                        break

                    illumination = glm.vec3()

                    # ambiant
                    illumination += (nearest_object.color * nearest_object.ambient) * light[
                        "ambient"
                    ]

                    # diffuse
                    illumination += (
                        (nearest_object.color * nearest_object.diffuse)
                        * light["diffuse"]
                        * glm.dot(intersection_to_light, normal_to_surface)
                    )

                    # specular
                    intersection_to_camera = glm.normalize(camera - intersection)
                    H = glm.normalize(intersection_to_light + intersection_to_camera)
                    illumination += (
                        (glm.vec3(1) * nearest_object.specular)
                        * light["specular"]
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
