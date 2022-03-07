class Camera:
    def __init__(self, cam):
        self.cam = cam
        self.position = self.cam.GetPosition()
        self.focal = self.cam.GetFocalPoint()
        self.clipping = self.cam.GetClippingRange()
        self.viewup = self.cam.GetViewUp()
        self.distance = self.cam.GetDistance()

    def get_orientation(self, caller, ev):
        self._orientation()

    def _orientation(self):
        self.position = self.cam.GetPosition()
        self.focal = self.cam.GetFocalPoint()
        self.clipping = self.cam.GetClippingRange()
        self.viewup = self.cam.GetViewUp()
        self.distance = self.cam.GetDistance()
        fmt2 = "{:9.6g}"
        print(", ".join(map(fmt2.format, self.position)))
