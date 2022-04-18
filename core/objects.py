from collections import namedtuple
import vtk, glm

Material = namedtuple("Material", ["ambient", "diffuse", "specular", "shininess", "reflection"])
Object = namedtuple("Object", ["data", "material", "position", "orientation"])


class Data:
    """
    Store vtkPolyData, normals and obbtree
    """

    def __init__(self, obj):
        if isinstance(obj.item, vtk.vtkPolyData):  # Planes
            polydata = obj.item
            normals = obj.item.GetPointData().GetNormals()
        elif isinstance(obj.item, vtk.vtkPLYReader):  # Ply object
            polydata = obj.item.GetOutput()
            normals = obj.item.GetOutput().GetPointData().GetNormals()
        else:  # Others
            polydata = obj.item.GetOutput()
            vtknormal = vtk.vtkPolyDataNormals()
            vtknormal.SetInputConnection(obj.item.GetOutputPort())
            vtknormal.ComputePointNormalsOn()
            vtknormal.ComputeCellNormalsOn()
            vtknormal.SplittingOff()
            vtknormal.FlipNormalsOff()
            vtknormal.AutoOrientNormalsOn()
            vtknormal.Update()
            normals = vtknormal.GetOutput().GetPointData().GetNormals()
        self.polydata = polydata
        self.normals = normals
        self.obbtree = obj.obbtree


class Material:
    """
    Store coefficients of material
    """

    def __init__(self, obj):
        color, ambient, diffuse, specular, shininess, reflection = obj.material
        self.ambient = color * ambient
        self.diffuse = color * diffuse
        self.specular = specular
        self.shininess = shininess
        self.reflection = reflection


class Light:
    def __init__(self, position):
        self.position = position
        self.ambient = glm.vec3(1)
        self.diffuse = glm.vec3(1)
        self.specular = glm.vec3(1)


class Scene:
    """
    Store all elements to deal with raytracing
    """

    def __init__(self, objects, actors, light, camera, display=True):
        pos = lambda actor: glm.vec3(actor.GetPosition())
        orient = lambda actor: glm.vec3(actor.GetOrientation())
        create = lambda obj, actor: Object(Data(obj), Material(obj), pos(actor), orient(actor))
        self.objects = [create(obj, actor) for obj, actor in zip(objects, actors)]
        self.light = Light(light.GetPosition())
        self.camera = glm.vec3(camera.GetPosition())
        if display:
            self.print_informations()

    def print_informations(self):
        print(f"Camera position: {self.camera}")
        print(f"Light position: {self.light.position}")
        for i, obj in enumerate(self.objects):
            print(f"Object {i} position: {obj.position}")
