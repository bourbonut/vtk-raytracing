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


keymap = {}
for key, value in vars(Qt).items():
    if isinstance(value, Qt.Key):
        keymap[value] = key.partition("_")[2]

modmap = {
    Qt.ControlModifier: keymap[Qt.Key_Control],
    Qt.AltModifier: keymap[Qt.Key_Alt],
    Qt.ShiftModifier: keymap[Qt.Key_Shift],
    Qt.MetaModifier: keymap[Qt.Key_Meta],
    Qt.GroupSwitchModifier: keymap[Qt.Key_AltGr],
    Qt.KeypadModifier: keymap[Qt.Key_NumLock],
}


def keyevent_to_string(event):
    sequence = []
    for modifier, text in modmap.items():
        if event.modifiers() & modifier:
            sequence.append(text)
    key = keymap.get(event.key(), event.text())
    if key not in sequence:
        sequence.append(key)
    return "+".join(sequence)


class Window(QWidget):
    def __init__(self):
        super(Window, self).__init__()
        self.frame = QtWidgets.QFrame()
        self.vtkWidget = QVTKRenderWindowInteractor(self.frame)

        grid = QGridLayout()
        grid.addWidget(self.vtkWidget)
        grid.addWidget(self.createExampleGroup())

        sphere1 = generate_sphere(50, 50)
        sphere2 = generate_sphere(50, 50, center=(0.0, 15.0, 0), radius=10.0)

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

        # renderWindow = vtk.vtkRenderWindow()
        # renderWindow.AddRenderer(renderer)
        #
        # renderWindowInteractor = vtk.vtkRenderWindowInteractor()
        #
        # renderWindowInteractor.SetRenderWindow(renderWindow)
        # renderWindowInteractor.Initialize()
        # renderWindowInteractor.Start()

        self.iren.Initialize()

        self.setLayout(grid)

        self.setWindowTitle("VTK Raytracing")
        self.resize(1200, 900)

    def keyPressEvent(self, event):
        print(keyevent_to_string(event))

    def change(self, i):
        print(i)

    def createExampleGroup(self):
        groupBox = QGroupBox("Slider Example")

        radio1 = QRadioButton("&Test")

        group = QGridLayout()

        spin1 = QDoubleSpinBox()
        spin1.textChanged.connect(self.change)
        spin2 = QDoubleSpinBox()
        spin2.textChanged.connect(self.change)
        spin3 = QDoubleSpinBox()
        spin3.textChanged.connect(self.change)

        slider = QSlider(Qt.Horizontal)
        slider.setFocusPolicy(Qt.StrongFocus)
        slider.setTickPosition(QSlider.TicksBothSides)
        slider.setTickInterval(10)
        slider.setSingleStep(1)

        radio1.setChecked(True)

        # group.addWidget(spin2, 2, 3)
        # group.addWidget(spin3, 3, 3)

        vbox = QGridLayout()
        vbox.addWidget(radio1, 0, 0, 1, 0, QtCore.Qt.AlignCenter)
        # vbox.addWidget(slider, 0, 0, 3, 0, QtCore.Qt.AlignCenter)
        vbox.addWidget(spin1, 2, 0)
        vbox.addWidget(spin2, 2, 1)
        vbox.addWidget(spin3, 2, 3)
        # vbox.addStretch(1)
        groupBox.setLayout(vbox)

        return groupBox


if __name__ == "__main__":
    app = QApplication(sys.argv)
    clock = Window()
    clock.show()
    sys.exit(app.exec_())
