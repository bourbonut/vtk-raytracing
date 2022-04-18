from gui import Window
from PyQt5.QtWidgets import QApplication
import sys
import json

if __name__ == "__main__":
    with open("config.json", "r") as f:
        configuration = json.load(f)
    app = QApplication(sys.argv)
    main_window = Window(configuration)
    main_window.show()
    sys.exit(app.exec_())
