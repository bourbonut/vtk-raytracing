from gui import Window, CurseApp
from PyQt5.QtWidgets import QApplication
import sys, json, curses

if __name__ == "__main__":
    cursesapp = curses.wrapper(CurseApp)
    selection_index = cursesapp.menu.position
    if selection_index != -1:
        selection = cursesapp.filenames[selection_index]
        with open(f"./configurations/{selection}", "r") as f:
            configuration = json.load(f)
        app = QApplication(sys.argv)
        main_window = Window(configuration)
        main_window.show()
        sys.exit(app.exec_())
