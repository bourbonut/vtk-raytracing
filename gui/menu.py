# From https://stackoverflow.com/questions/14200721/how-to-create-a-menu-and-submenus-in-python-curses
import curses
from .describer import describe
from curses import panel
from pathlib import Path


class Menu(object):
    def __init__(self, items, stdscreen):
        self.window = stdscreen.subwin(0, 0)
        self.window.keypad(1)
        self.panel = panel.new_panel(self.window)
        self.panel.hide()
        panel.update_panels()

        self.position = 0
        self.items = items
        self.items.append(["exit", "exit"])

    def navigate(self, n):
        self.position += n
        if self.position < 0:
            self.position = 0
        elif self.position >= len(self.items):
            self.position = len(self.items) - 1

    def display(self):
        self.panel.top()
        self.panel.show()
        self.window.clear()

        while True:
            self.window.refresh()
            curses.doupdate()
            for index, item in enumerate(self.items):
                if index == self.position:
                    mode = curses.A_REVERSE
                else:
                    mode = curses.A_NORMAL

                msg = "%d. %s" % (index, item[0])
                self.window.addstr(1 + index, 1, msg, mode)

            key = self.window.getch()

            if key in [curses.KEY_ENTER, ord("\n")]:
                if self.position == len(self.items) - 1:
                    self.position = -1
                break

            elif key == curses.KEY_UP:
                self.navigate(-1)

            elif key == curses.KEY_DOWN:
                self.navigate(1)

            elif key == curses.KEY_RIGHT:
                self.items[self.position][1]()

        self.window.clear()
        self.panel.hide()
        panel.update_panels()
        curses.doupdate()


class Describer(object):
    def __init__(self, items, stdscreen):
        self.window = stdscreen.subwin(0, 0)
        self.window.keypad(1)
        self.panel = panel.new_panel(self.window)
        self.panel.hide()
        panel.update_panels()

        self.position = 0
        self.items = items

    def navigate(self, n):
        self.position += n
        if self.position < 0:
            self.position = 0
        elif self.position >= len(self.items):
            self.position = len(self.items) - 1

    def display(self):
        self.panel.top()
        self.panel.show()
        self.window.clear()

        while True:
            self.window.refresh()
            curses.doupdate()
            for index, item in enumerate(self.items):
                if index == self.position:
                    mode = curses.A_REVERSE
                else:
                    mode = curses.A_NORMAL

                msg = "%s" % (item)
                self.window.addstr(1 + index, 1, msg, mode)

            key = self.window.getch()

            if key in [curses.KEY_ENTER, ord("\n")]:
                if self.position == len(self.items) - 1:
                    self.position = -1
                break

            elif key == curses.KEY_UP:
                break

            elif key == curses.KEY_DOWN:
                break

            elif key == curses.KEY_LEFT:
                break

        self.window.clear()
        self.panel.hide()
        panel.update_panels()
        curses.doupdate()


class CurseApp(object):
    def __init__(self, stdscreen):
        self.screen = stdscreen
        curses.curs_set(0)
        path = Path().absolute() / "configurations"
        self.filenames = [file.name for file in path.iterdir()]
        submenu = lambda file: Describer(describe(file), self.screen).display
        self.submenus = map(submenu, self.filenames)
        self.menu = Menu(list(zip(self.filenames, self.submenus)), self.screen)
        self.menu.display()
