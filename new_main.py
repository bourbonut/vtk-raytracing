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
        grid.addWidget(self.vtkWidget)
        for actor, label in zip(self.actors, self.labels):
            grid.addWidget(self.create_coord(actor, label))

        grid.addWidget(self.create_coord(self.light, "Light"))

        button = QPushButton()
        button.setText("Raytracing")
        button.clicked.connect(self.button_action)
        grid.addWidget(button)

        self.setLayout(grid)

        self.setWindowTitle("VTK Raytracing")
        self.resize(900, 1000)

    def generate_objects(self):
        s1 = generate_sphere(20, 20, center=(-0.2, 0, -1), radius=0.7)
        s2 = generate_sphere(20, 20, center=(0.1, -0.3, 0), radius=0.1)
        s3 = generate_sphere(20, 20, center=(-0.3, 0, 0), radius=0.15)
        plane, obbtree = generate_plane(20, -0.7)

        vec3 = glm.vec3
        obbtrees = [make_obbtree(obj) for obj in (s1, s2, s3)] + [obbtree]
        obj1 = Object(s1, obbtrees[0], vec3(1, 0, 0), 0.1, 0.7, 1, 100, 0.5, vec3(-0.2, 0, -1))
        obj2 = Object(s2, obbtrees[1], vec3(1, 0, 1), 0.1, 0.7, 1, 100, 0.5, vec3(0.1, -0.3, 0))
        obj3 = Object(s3, obbtrees[2], vec3(0, 1, 0), 0.1, 0.6, 1, 100, 0.5, vec3(-0.3, 0, 0))
        obj4 = Object(plane, obbtrees[3], vec3(1, 1, 1), 0.1, 0.6, 1, 100, 0.5, vec3(0, 0, 0))

        self.objects = [obj1, obj2, obj3, obj4]
        self.labels = ("Red sphere", "Violet sphere", "Green sphere", "White plane")

    def setup_objects(self):
        self.actors = []
        for i, obj in enumerate(self.objects):
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
            actor.AddPosition(obj.position)
            self.actors.append(actor)
            self.renderer.AddActor(actor)

    def setup_camera(self):
        vtkcamera = vtk.vtkCamera()
        self.renderer.SetActiveCamera(vtkcamera)
        self.camera = Camera(self.renderer.GetActiveCamera())
        self.iren.AddObserver("EndInteractionEvent", self.camera.get_orientation)

    def setup_light(self):
        self.light = vtk.vtkLight()
        self.light.SetPosition([5, 5, 5])
        self.light.SetConeAngle(30)
        self.light.SetFocalPoint(self.actors[0].GetPosition())
        self.light.PositionalOn()
        self.renderer.AddLight(self.light)
        self.light_actor = vtk.vtkLightActor()
        self.light_actor.SetLight(self.light)
        self.renderer.AddViewProp(self.light_actor)
        self.renderer.UseShadowsOn()

    def change_spin(self, value, obj, index):
        coord = list(obj.GetPosition())
        coord[index] = float(value.replace(",", "."))
        obj.SetPosition(*coord)
        self.vtkWidget.GetRenderWindow().Render()

    def create_coord(self, actor, title):
        groupBox = QGroupBox(title)

        radio = QRadioButton("&Activate")
        radio.setChecked(True)

        coord = list(actor.GetPosition())

        spins = [QDoubleSpinBox() for _ in range(3)]
        for i, spin in enumerate(spins):
            spin.setMinimum(-500)
            spin.setValue(coord[i])
            f = partial(self.change_spin, obj=actor, index=i)
            spins[i].textChanged.connect(f)

        slider = QSlider(Qt.Horizontal)
        slider.setFocusPolicy(Qt.StrongFocus)
        slider.setTickPosition(QSlider.TicksBothSides)
        slider.setTickInterval(10)
        slider.setSingleStep(1)

        box = QGridLayout()
        # box.addWidget(radio, 0, 1, QtCore.Qt.AlignCenter)
        for i, spin in enumerate(spins):
            box.addWidget(spin, 2, i)
        box.addWidget(slider, 3, 0, 3, 0)
        groupBox.setLayout(box)

        return groupBox

    def button_action(self):
        image = generate_image(self.objects, self.light, self.camera)
        plt.imsave("poutine.png", image)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    clock = Window()
    clock.show()
    sys.exit(app.exec_())
