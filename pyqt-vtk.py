from collections import namedtuple
import vtk
import sys
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5 import QtCore
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QMenu,
    QPushButton,
    QRadioButton,
    QDoubleSpinBox,
    QVBoxLayout,
    QWidget,
    QSlider,
)
from functools import partial

from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor


Sphere = namedtuple("Sphere", ["source", "mapper", "actor"])


def generate_sphere(phi, theta, center=(0.0, 0.0, 0.0), radius=5.0):
    source = vtk.vtkSphereSource()
    mapper = vtk.vtkPolyDataMapper()
    actor = vtk.vtkActor()

    source.SetCenter(*center)
    source.SetRadius(radius)
    source.SetPhiResolution(phi)
    source.SetThetaResolution(theta)
    mapper.SetInputConnection(source.GetOutputPort())
    actor.SetMapper(mapper)

    return Sphere(source, mapper, actor)


class Window(QWidget):
    def __init__(self):
        super(Window, self).__init__()
        self.frame = QtWidgets.QFrame()
        self.vtkWidget = QVTKRenderWindowInteractor(self.frame)

        sphere1 = generate_sphere(50, 50)
        sphere2 = generate_sphere(50, 50, center=(0.0, 15.0, 0), radius=10.0)
        self.sphere = sphere1

        grid = QGridLayout()
        grid.addWidget(self.vtkWidget)
        grid.addWidget(self.create_coord("Lumiere"))

        button = QPushButton()
        button.setText("Raytracing")
        button.clicked.connect(self.button_action)
        grid.addWidget(button)

        sphere1.actor.GetProperty().SetColor(1, 1, 1)
        sphere2.actor.GetProperty().SetColor(1, 0, 0)

        colors = vtk.vtkNamedColors()

        renderer = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(renderer)
        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()
        renderer.AddActor(sphere1.actor)
        renderer.AddActor(sphere2.actor)
        renderer.SetBackground(colors.GetColor3d("Black"))
        renderer.ResetCamera()

        self.iren.Initialize()

        self.setLayout(grid)

        self.setWindowTitle("VTK Raytracing")
        self.resize(900, 600)

    def change_spin(self, value, obj, index):
        coord = list(obj.GetCenter())
        coord[index] = float(value.replace(",", "."))
        obj.SetCenter(*coord)
        self.vtkWidget.GetRenderWindow().Render()

    def create_coord(self, title):
        groupBox = QGroupBox(title)

        radio = QRadioButton("&Activate")
        radio.setChecked(True)

        spins = [QDoubleSpinBox() for _ in range(3)]
        for i, spin in enumerate(spins):
            spin.setMinimum(-500)
            f = partial(self.change_spin, obj=self.sphere.source, index=i)
            spins[i].textChanged.connect(f)

        # self.sphere.source

        slider = QSlider(Qt.Horizontal)
        slider.setFocusPolicy(Qt.StrongFocus)
        slider.setTickPosition(QSlider.TicksBothSides)
        slider.setTickInterval(10)
        slider.setSingleStep(1)

        box = QGridLayout()
        box.addWidget(radio, 0, 1, QtCore.Qt.AlignCenter)
        for i, spin in enumerate(spins):
            box.addWidget(spin, 2, i)
        box.addWidget(slider, 3, 0, 3, 0)
        groupBox.setLayout(box)

        return groupBox

    def button_action(self):
        print("ok")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    clock = Window()
    clock.show()
    sys.exit(app.exec_())
