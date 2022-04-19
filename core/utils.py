import glm
from math import acos


def reflected(vector, axis):
    return vector - 2 * glm.dot(vector, axis) * axis


def change_reference(ref):
    """
    Change reference
    """
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


def interpolation(points, normals, target):
    """
    Return interpolated normal
    """
    A, B, C = map(glm.vec3, points)
    normals = list(map(glm.vec3, normals))
    target = glm.vec3(target)
    AC = A - C
    BC = B - C
    TC = target - C
    u, v, _ = glm.inverse(glm.mat3(AC, BC, glm.cross(AC, BC))) * TC
    w = 1 - u - v
    return u * normals[0] + v * normals[1] + w * normals[2]
