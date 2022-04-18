from core import generate_image, Scene
from .generators import *
from functools import partial

from matplotlib import pyplot as plt
import glm


from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5 import QtCore
from PyQt5.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QRadioButton,
    QDoubleSpinBox,
    QWidget,
    QSlider,
)


class Camera(vtk.vtkCamera):
    def __init__(self):
        super().__init__()
        self.position = self.GetPosition()
        self.focal = self.GetFocalPoint()
        self.clipping = self.GetClippingRange()
        self.viewup = self.GetViewUp()
        self.distance = self.GetDistance()

    def get_orientation(self, caller, ev):
        self._orientation()

    def _orientation(self):
        self.position = self.GetPosition()
        self.focal = self.GetFocalPoint()
        self.clipping = self.GetClippingRange()
        self.viewup = self.GetViewUp()
        self.distance = self.GetDistance()
        fmt2 = "{:9.6g}"
        print(", ".join(map(fmt2.format, self.position)))


class Window(QWidget):
    def __init__(self, config):
        super(Window, self).__init__()
        self.width, self.height, self.zoom, self.max_depth = config["scene"]
        data = generate_data(config["objects"], config["labels"])
        self.objects, self.labels, self.actors = data

        self.initialize()
        self.set_camera(config["camera"])
        self.set_light(self.actors[config["target"]], *config["light"])
        self.set_widgets()

        self.setWindowTitle("VTK Raytracing")
        self.resize(1500, 800)

    def initialize(self):
        colors = vtk.vtkNamedColors()
        self.frame = QtWidgets.QFrame()
        self.vtkWidget = QVTKRenderWindowInteractor(self.frame)
        self.renderer = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)
        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()
        self.renderer.SetBackground(colors.GetColor3d("Black"))
        self.renderer.ResetCamera()
        for actor in self.actors:
            self.renderer.AddActor(actor)
        self.iren.Initialize()

    def set_camera(self, position):
        self.camera = Camera()
        self.renderer.SetActiveCamera(self.camera)
        self.camera.SetPosition(glm.vec3(position) * self.zoom * 5)  # offset = 5
        self.iren.AddObserver("EndInteractionEvent", self.camera.get_orientation)

    def set_light(self, target, position, angle):
        self.light = vtk.vtkLight()
        self.light.SetPosition(position)
        self.light.SetConeAngle(angle)
        self.light.SetFocalPoint(target.GetPosition())
        self.light.PositionalOn()
        self.light_actor = vtk.vtkLightActor()
        self.light_actor.SetLight(self.light)
        self.renderer.AddLight(self.light)
        self.renderer.AddViewProp(self.light_actor)
        self.renderer.UseShadowsOn()

    def set_widgets(self):
        grid = QGridLayout()
        self.n_widgets = 0
        grid.addWidget(self.vtkWidget, 0, 0, 0, 1)
        position = self.change_spin_position
        orientation = self.change_spin_orientation
        functions = [
            self.change_spin_position,
            self.change_spin_orientation,
            self.change_slider_scale,
            lambda obj: obj.GetScale()[0] * 10,
        ]
        for actor, label in zip(self.actors, self.labels):
            grid = self.add_widget(grid, self.create_coord(actor, label, functions))

        functions = [
            self.change_spin_position,
            None,
            self.change_slider_intensity,
            lambda obj: obj.GetIntensity() * 10,
        ]
        grid = self.add_widget(grid, self.create_coord(self.light, "Light", functions))

        button = QPushButton()
        button.setText("Raytracing")
        button.clicked.connect(self.button_action)
        grid = self.add_widget(grid, button)

        self.setLayout(grid)

    def add_widget(self, grid, widget):
        grid.addWidget(widget, self.n_widgets, 1)
        self.n_widgets += 1
        return grid

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
        obj.SetScale(value / 10)
        self.vtkWidget.GetRenderWindow().Render()

    def change_slider_intensity(self, value, obj):
        obj.SetIntensity(value / 10)
        self.vtkWidget.GetRenderWindow().Render()

    def generate_spins(self, obj, function, coords):
        spins = [QDoubleSpinBox() for _ in range(3)]
        for i, spin in enumerate(spins):
            spin.setMinimum(-5000)
            spin.setMaximum(5000)
            spin.setValue(coords[i])
            f = partial(function, obj=obj, index=i)
            spins[i].textChanged.connect(f)
        return spins

    def create_coord(self, obj, title, functions):
        groupBox = QGroupBox(title)

        box = QGridLayout()
        spins = {}
        slider = None
        if functions[0]:  # Spin Position
            coords = list(obj.GetPosition())
            spins["position"] = self.generate_spins(obj, functions[0], coords)
        if functions[1]:  # Spin Orientation
            coords = list(obj.GetOrientation())
            spins["orientation"] = self.generate_spins(obj, functions[1], coords)
        if functions[2]:  # Slider
            slider = QSlider(Qt.Horizontal)
            slider.setFocusPolicy(Qt.StrongFocus)
            slider.setTickPosition(QSlider.TicksBothSides)
            slider.setTickInterval(10)
            slider.setSingleStep(1)
            slider.setValue(functions[3](obj))
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

        if slider:
            box.addWidget(slider, 4, 0, 4, 0)
        groupBox.setLayout(box)

        return groupBox

    def button_action(self):
        scene = Scene(self.objects, self.actors, self.light, self.camera)
        image = generate_image(scene, self.max_depth, self.width, self.height, self.zoom)
        plt.imsave("./images/output.png", image)
        print("Saved.")
