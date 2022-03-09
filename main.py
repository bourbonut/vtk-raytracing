import vtk
from tools import *
from tools.raytracing import *
from rich.progress import Progress
import glm
import numpy as np
from matplotlib import pyplot as plt


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


s1 = generate_sphere(3 * 50, 3 * 50, center=(-0.2, 0, -1), radius=0.7)
s2 = generate_sphere(3 * 50, 3 * 50, center=(0.1, -0.3, 0), radius=0.1)
s3 = generate_sphere(3 * 50, 3 * 50, center=(-0.3, 0, 0), radius=0.15)
# s4 = generate_sphere(50, 50, center=(0, -9000, 0), radius=9000 - 0.7)
plane, obbtree = generate_plane(9000, -0.7)

obbtrees = [make_obbtree(obj) for obj in (s1, s2, s3)] + [obbtree]


objects = [
    Object(s1, obbtrees[0], glm.vec3(1, 0, 0), 0.1, 0.7, 1, 100, 0.5, glm.vec3(-0.2, 0, -1)),
    Object(s2, obbtrees[1], glm.vec3(1, 0, 1), 0.1, 0.7, 1, 100, 0.5, glm.vec3(0.1, -0.3, 0)),
    Object(s3, obbtrees[2], glm.vec3(0, 1, 0), 0.1, 0.6, 1, 100, 0.5, glm.vec3(-0.3, 0, 0)),
    Object(plane, obbtrees[3], glm.vec3(1, 1, 1), 0.1, 0.6, 1, 100, 0.5, glm.vec3(0, -9000, 0)),
]

ren = vtk.vtkRenderer()

for i, obj in enumerate(objects):
    mapper = vtk.vtkPolyDataMapper()
    if i != 3:
        mapper.SetInputConnection(obj.obj.GetOutputPort())
    else:
        mapper.SetInputData(obj.obj)
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(obj.color)
    actor.GetProperty().SetAmbient(obj.ambient)
    actor.GetProperty().SetDiffuse(obj.diffuse)
    actor.GetProperty().SetSpecular(obj.specular)
    # actor.AddPosition(obj.position)
    ren.AddActor(actor)

renWin = vtk.vtkRenderWindow()
renWin.AddRenderer(ren)
iren = vtk.vtkRenderWindowInteractor()
iren.SetRenderWindow(renWin)

vtkcamera = vtk.vtkCamera()
ren.SetActiveCamera(vtkcamera)
cam = Camera(ren.GetActiveCamera())
iren.AddObserver("EndInteractionEvent", cam.get_orientation)

renWin.SetSize(512, 512)
renWin.Render()
renWin.SetWindowName("CallBack")

iren.Initialize()
iren.Start()

raise

width = 300 * 3
height = 200 * 3
max_depth = 3

# camera = glm.vec3(cam.position)
camera = glm.vec3(0, 0, 1)
ratio = width / height
screen = (-1, 1 / ratio, 1, -1 / ratio)


light = {
    "position": glm.vec3(5, 5, 5),
    "ambient": glm.vec3(1, 1, 1),
    "diffuse": glm.vec3(1, 1, 1),
    "specular": glm.vec3(1, 1, 1),
}

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
                intersection_to_light_distance = glm.length(light["position"] - intersection)
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

plt.imsave("poutine.png", image)
