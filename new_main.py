from matplotlib import pyplot as plt
import glm

from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5 import QtCore
from PyQt5.QtWidgets import (
    QApplication,
    QGridLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QRadioButton,
    QDoubleSpinBox,
    QWidget,
    QSlider,
)

import sys
from functools import partial
from tools import *


class Window(QWidget):
    def __init__(self):
        super(Window, self).__init__()
        self.generate_objects()

        self.frame = QtWidgets.QFrame()
        self.vtkWidget = QVTKRenderWindowInteractor(self.frame)

        colors = vtk.vtkNamedColors()

        self.renderer = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)
        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()
        self.setup_objects()
        self.setup_camera()
        self.setup_light()
        self.renderer.SetBackground(colors.GetColor3d("Black"))
        # self.renderer.SetBackground2(colors.GetColor3d("Black"))
        # self.renderer.SetBackground(colors.GetColor3d("Silver"))
        # self.renderer.SetGradientBackground(True)
        self.renderer.ResetCamera()

        self.iren.Initialize()

        grid = QGridLayout()
        grid.addWidget(self.vtkWidget, 0, 0, 1, 0)
        position = self.change_spin_position
        orientation = self.change_spin_orientation
        functions = [
            self.change_spin_position,
            self.change_spin_orientation,
            self.change_slider_scale,
        ]
        for actor, label in zip(self.actors, self.labels):
            grid.addWidget(self.create_coord(actor, label, functions))

        functions = [self.change_spin_position, None, self.change_slider_intensity]
        grid.addWidget(self.create_coord(self.light, "Light", functions))

        button = QPushButton()
        button.setText("Raytracing")
        button.clicked.connect(self.button_action)
        grid.addWidget(button)

        self.setLayout(grid)

        self.setWindowTitle("VTK Raytracing")
        self.resize(900, 1000)

    def generate_objects(self):
        # s1 = generate_sphere(20, 20, center=(-0.2, 0, -1), radius=0.7)
        bgear, obbtree_bgear = open_stl("bevel_gear2.stl")
        s2 = generate_sphere(20, 20, center=(0.1, -0.3, 0), radius=5)
        s3 = generate_sphere(20, 20, center=(-0.3, 0, 0), radius=5)
        plane, obbtree = generate_plane(100, -20)

        vec3 = glm.vec3
        obbtrees = [
            obbtree_bgear,
            obbtree,
        ]  # + [make_obbtree(obj) for obj in (s2, s3)] + [obbtree]
        obj1 = Object(bgear, obbtrees[0], vec3(1, 1, 1), 0.1, 0.7, 1, 100, 0.5, vec3(0, 0, 0))
        # obj2 = Object(s2, obbtrees[1], vec3(1, 0, 1), 0.1, 0.7, 1, 100, 0.5, vec3(0.1, -0.3, 0))
        # obj3 = Object(s3, obbtrees[2], vec3(0, 1, 0), 0.1, 0.6, 1, 100, 0.5, vec3(-6, 0, 0))
        obj4 = Object(plane, obbtrees[1], vec3(1, 1, 1), 0.1, 0.6, 1, 100, 0.5, vec3(0, 0, 0))

        self.objects = [obj1, obj4]
        self.labels = ("Bevel gear", "White plane")  # "Violet sphere", "Green sphere",

    def setup_objects(self):
        self.actors = []
        for i, obj in enumerate(self.objects):
            mapper = vtk.vtkPolyDataMapper()
            if isinstance(obj.obj, vtk.vtkPolyData):
                mapper.SetInputData(obj.obj)
            else:
                mapper.SetInputConnection(obj.obj.GetOutputPort())
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(obj.color)
            actor.GetProperty().SetAmbient(obj.ambient)
            actor.GetProperty().SetDiffuse(obj.diffuse)
            actor.GetProperty().SetSpecular(obj.specular)
            actor.AddPosition(obj.position)
            self.actors.append(actor)
            self.renderer.AddActor(actor)

    def setup_camera(self):
        vtkcamera = vtk.vtkCamera()
        self.renderer.SetActiveCamera(vtkcamera)
        self.camera = Camera(self.renderer.GetActiveCamera())
        self.camera.cam.SetPosition(0, 0.5, 1)
        self.camera.position = self.camera.cam.GetPosition()
        self.iren.AddObserver("EndInteractionEvent", self.camera.get_orientation)

    def setup_light(self):
        self.light = vtk.vtkLight()
        self.light.SetPosition([0, 12, 14])
        self.light.SetConeAngle(30)
        self.light.SetFocalPoint(self.actors[0].GetPosition())
        self.light.PositionalOn()
        self.renderer.AddLight(self.light)
        self.light_actor = vtk.vtkLightActor()
        self.light_actor.SetLight(self.light)
        self.renderer.AddViewProp(self.light_actor)
        self.renderer.UseShadowsOn()

    def change_spin_position(self, value, obj, index):
        coord = list(obj.GetPosition())
        coord[index] = float(value.replace(",", "."))
        obj.SetPosition(*coord)
        self.vtkWidget.GetRenderWindow().Render()

    def change_spin_orientation(self, value, obj, index):
        coord = list(obj.GetOrientation())
        coord[index] = float(value.replace(",", "."))
        obj.SetOrientation(*coord)
        self.vtkWidget.GetRenderWindow().Render()

    def change_slider_scale(self, value, obj):
        obj.SetScale(value)
        self.vtkWidget.GetRenderWindow().Render()

    def change_slider_intensity(self, value, obj):
        obj.SetIntensity(value)
        self.vtkWidget.GetRenderWindow().Render()

    def generate_spins(self, obj, function, coords):
        spins = [QDoubleSpinBox() for _ in range(3)]
        for i, spin in enumerate(spins):
            spin.setMinimum(-50000)
            spin.setValue(coords[i])
            f = partial(function, obj=obj, index=i)
            spins[i].textChanged.connect(f)
        return spins

    def create_coord(self, obj, title, functions):
        groupBox = QGroupBox(title)

        radio = QRadioButton("&Activate")
        radio.setChecked(True)

        box = QGridLayout()
        spins = {}
        slider = None
        if functions[0]:
            coords = list(obj.GetPosition())
            spins["position"] = self.generate_spins(obj, functions[0], coords)
        if functions[1]:
            coords = list(obj.GetOrientation())
            spins["orientation"] = self.generate_spins(obj, functions[1], coords)
        if functions[2]:
            slider = QSlider(Qt.Horizontal)
            slider.setFocusPolicy(Qt.StrongFocus)
            slider.setTickPosition(QSlider.TicksBothSides)
            slider.setTickInterval(10)
            slider.setSingleStep(1)
            f = partial(functions[2], obj=obj)
            slider.valueChanged.connect(f)

        i = 0
        j = 0
        for key in spins:
            label = QLabel(key.title())
            box.addWidget(label, 2, j)
            for spin in spins[key]:
                box.addWidget(spin, 3, i)
                i += 1
            j += 3

        # box.addWidget(radio, 0, 1, QtCore.Qt.AlignCenter)
        if slider:
            box.addWidget(slider, 4, 0, 4, 0)
        groupBox.setLayout(box)

        return groupBox

    def button_action(self):
        image = generate_image(
            self.objects, self.actors, self.light, self.camera, width=300 * 3, height=200 * 3
        )
        plt.imsave("poutine.png", image)
        print("Saved.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    clock = Window()
    clock.show()
    sys.exit(app.exec_())
