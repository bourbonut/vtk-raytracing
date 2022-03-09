import vtk

colors = vtk.vtkNamedColors()

backgroundColors = list()
backgroundColors.append(colors.GetColor3d("Cornsilk"))
backgroundColors.append(colors.GetColor3d("NavajoWhite"))
backgroundColors.append(colors.GetColor3d("Tan"))

ren = list()
ren.append(vtk.vtkRenderer())
ren.append(vtk.vtkRenderer())
ren.append(vtk.vtkRenderer())
ren[0].SetViewport(0, 0, 1.0 / 3.0, 1)  # Input
ren[1].SetViewport(1.0 / 3.0, 0, 2.0 / 3.0, 1)  # Normals (no split)
ren[2].SetViewport(2.0 / 3.0, 0, 1, 1)  # Normals (split)

# reader = vtk.vtkSTLReader()
# reader.SetFileName("bevel_gear.stl")
filename = "bevel_gear.stl"
reader = vtk.vtkSTLReader()
reader.SetFileName(filename)
reader.Update()
poly_data = reader.GetOutput()

# ren = vtk.vtkRenderer()
camera = vtk.vtkCamera()

normals = vtk.vtkPolyDataNormals()
normals.SetInputData(reader.GetOutput())
normals.SetFeatureAngle(30.0)
for i in range(3):
    if i == 0:
        normals.ComputePointNormalsOff()
    elif i == 1:
        normals.ComputePointNormalsOn()
        normals.SplittingOff()
    else:
        normals.ComputeCellNormalsOn()
        normals.SplittingOn()

    normals.Update()
    normalsPolyData = vtk.vtkPolyData()
    normalsPolyData.DeepCopy(normals.GetOutput())
    print(normalsPolyData.GetCellData().GetNormals())

    # mapper
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(normalsPolyData)
    mapper.ScalarVisibilityOff()

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetDiffuseColor(colors.GetColor3d("Peacock"))
    actor.GetProperty().SetDiffuse(0.7)
    actor.GetProperty().SetSpecularPower(20)
    actor.GetProperty().SetSpecular(0.5)

    # add the actor
    ren[i].SetBackground(backgroundColors[i])
    ren[i].SetActiveCamera(camera)
    ren[i].AddActor(actor)

# mapper = vtk.vtkPolyDataMapper()
# mapper.SetInputConnection(reader.GetOutputPort())
#
# actor = vtk.vtkActor()
# actor.SetMapper(mapper)
# actor.GetProperty().SetDiffuse(0.8)
# actor.GetProperty().SetDiffuseColor(colors.GetColor3d("LightSteelBlue"))
# actor.GetProperty().SetSpecular(0.3)
# actor.GetProperty().SetSpecularPower(60.0)
#
# ren.AddActor(actor)

# renWin = vtk.vtkRenderWindow()
# renWin.AddRenderer(ren)
# iren = vtk.vtkRenderWindowInteractor()
# iren.SetRenderWindow(renWin)
#
#
# renWin.SetSize(512, 512)
# renWin.Render()
# renWin.SetWindowName("CallBack")
#
# iren.Initialize()
# iren.Start()

renwin = vtk.vtkRenderWindow()
renwin.AddRenderer(ren[0])
renwin.AddRenderer(ren[1])
renwin.AddRenderer(ren[2])
renwin.SetWindowName("NormalsDemo")

# An interactor.
interactor = vtk.vtkRenderWindowInteractor()
interactor.SetRenderWindow(renwin)

renwin.SetSize(900, 300)
ren[0].GetActiveCamera().SetFocalPoint(0, 0, 0)
ren[0].GetActiveCamera().SetPosition(1, 0, 0)
ren[0].GetActiveCamera().SetViewUp(0, 0, -1)
ren[0].ResetCamera()

ren[0].GetActiveCamera().Azimuth(120)
ren[0].GetActiveCamera().Elevation(30)
ren[0].GetActiveCamera().Dolly(1.1)
ren[0].ResetCameraClippingRange()

renwin.Render()
ren[0].ResetCamera()
renwin.Render()

# Start.
interactor.Initialize()
interactor.Start()
