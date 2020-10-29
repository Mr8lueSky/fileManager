import pygame
import threading
from pygame.locals import *
import subprocess
import os
import sys


def thread(func, args=[], kwargs={}):
    threading.Thread(target=func, args=args, kwargs=kwargs).start()


def dec_thread(function_to_decorate):
    def a_wrapper_accepting_arguments(*args, **kwargs): # аргументы прибывают отсюда
        thread(function_to_decorate, args=list(args), kwargs=kwargs)
    return a_wrapper_accepting_arguments


# 640 x 480
class Window:
    def __init__(self, width, height):
        pygame.init()
        self.screen_size = (width, height)
        self.screen = pygame.display.set_mode(self.screen_size)
        self.clock = None
        self.objects = []
        self.tick = 30
        self.active = False
        self.clicked = False

    def add_object(self, object):
        if object in self.objects:
            return None
        self.objects.append(object)
        object.parent = self

    def event_handler(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                self.close()
            if event.type == MOUSEBUTTONDOWN and not(pygame.mouse.get_pressed()[0]):
                mouse_pos = pygame.mouse.get_pos()
                for object in self.objects:
                    if (object.pos[0] < mouse_pos[0] < object.pos[0] + object.size[0]) and \
                            (object.pos[1] < mouse_pos[1] < object.pos[1] + object.size[1]):
                        object.on_mwheel(True if event.button == 4 else False)
                        return True

    def click_handler(self):
        if not(pygame.mouse.get_pressed()[0]):
            self.clicked = False
        mouse_pos = pygame.mouse.get_pos()
        for object in self.objects:
            if (object.pos[0] < mouse_pos[0] < object.pos[0] + object.size[0]) and \
            (object.pos[1] < mouse_pos[1] < object.pos[1] + object.size[1]) and \
            pygame.mouse.get_pressed()[0] and not(self.clicked):
                object.on_click(mouse_pos)
                self.clicked = True
                return True

    def draw(self):
        self.screen.fill(pygame.color.THECOLORS["black"])
        for object in self.objects:
            self.screen.blit(object.image, object.pos)
        pygame.display.flip()

    def show(self):
        clock = pygame.time.Clock()
        self.active = True
        while True:
            clock.tick(self.tick)
            self.event_handler()
            self.click_handler()
            self.draw()

    def close(self):
        self.active = False
        exit(0)

    def mouse_pos(self):
        return pygame.mouse.get_pos()


class GraphicalObject:
    def __init__(self, width, height, pos, color="red"):
        self.size = (width, height)
        self.pos = pos
        self.color = color
        self.background = pygame.color.THECOLORS[color]
        self.image = pygame.Surface(self.size).convert()
        self.image.fill(self.background)
        self.parent = None

    def on_click(self, coordinates):
        print("Clicked!")


class File(GraphicalObject):
    def __init__(self, path, width=640, height=35, pos=(0, 0), color="green"):
        super(File, self).__init__(width, height, pos, color=color)
        self.path = path
        f1 = pygame.font.Font(None, 40)
        self.name = self.path[self.path.rfind("\\") + 1:]
        text1 = f1.render(self.name, 1, (0, 0, 0))
        self.image.blit(text1, (5, 3))

    @dec_thread
    def on_click(self, coordinates):
        if isinstance(self.parent, FileList) and self.path[1] != ":":
            subprocess.Popen(self.parent.curr_path + self.path, shell=True)
        else:
            subprocess.Popen(self.path, shell=True)


class Folder(GraphicalObject):
    def __init__(self, path, name=None, width=640, height=35, pos=(0, 0), color="blue"):
        super(Folder, self).__init__(width, height, pos, color=color)
        self.path = path
        self.name = path[path.rfind("\\") + 1:] if name is None else name
        f1 = pygame.font.Font(None, 40)
        text1 = f1.render(self.name, 1, (0, 0, 0))
        self.image.blit(text1, (5, 3))

    def on_click(self, coordinates):
        if isinstance(self.parent, FileList):
            self.parent.change_dir(self.path)


class List(GraphicalObject):
    def __init__(self, width=640, height=0, pos=(0, 0), color="white"):
        super(List, self).__init__(width, height, pos, color="white")
        self.size = (width, height)
        self.objects = []
        self.pos = pos
        self.margin = 5
        self.mwheel_speed = 35 + self.margin

    def add_object(self, object):
        if object in self.objects:
            return None
        self.objects.append(object)
        height = 0
        for object in self.objects:
            height += object.size[1]
        height += (len(self.objects) - 1) * self.margin
        self.size = (self.size[0], height)

        self.refactor()
        object.parent = self

    def refactor(self):
        self.image = pygame.Surface(self.size).convert()
        self.image.fill(self.background)

        height = 0
        for object in self.objects:
            object.pos = (self.pos[0], height)
            self.image.blit(object.image, (0, height))
            height += object.size[1] + self.margin

    def on_click(self, coordinates):
        mouse_pos = pygame.mouse.get_pos()
        for object in self.objects:
            if (object.pos[0] < mouse_pos[0] < object.pos[0] + object.size[0]) and \
            (object.pos[1] < mouse_pos[1] < object.pos[1] + object.size[1]) and \
            pygame.mouse.get_pressed()[0]:
                object.on_click(mouse_pos)
                return True

    def on_mwheel(self, direction):
        if direction:
            if self.pos[1] < 0:
                self.pos = (self.pos[0], self.pos[1] + self.mwheel_speed)
                for object in self.objects:
                    object.pos = (object.pos[0], object.pos[1] + self.mwheel_speed)
        else:
            if self.pos[1] + self.size[1] > self.parent.screen_size[1]:
                self.pos = (self.pos[0], self.pos[1] - self.mwheel_speed)
                for object in self.objects:
                    object.pos = (object.pos[0], object.pos[1] - self.mwheel_speed)


class FileList(List):
    def __init__(self, width=640, height=0, pos=(0, 0)):
        super(FileList, self).__init__(width, height, pos, color="white")
        self.drivers = []
        self.load_drivers()
        self.curr_path = self.drivers[0] + ":\\"
        self.make_file_tree()

    def load_drivers(self):
        self.drivers.clear()
        for code in range(97, 97 + 26):
            check = subprocess.Popen("if exist " + chr(code) + ":\*.* echo 1", shell=True, stdout=subprocess.PIPE)
            if check.communicate()[0] == b'1\r\n':
                self.drivers.append(chr(code).upper())

    def make_file_tree(self):
        self.objects.clear()
        if self.curr_path:
            self.add_object(Folder(self.curr_path[:-1][:self.curr_path[:-1].rfind("\\") + 1], name=".."))
            files = os.listdir(self.curr_path)
            for file in files:
                path = self.curr_path + file
                if os.path.isdir(path):
                    self.add_object(Folder(path))
                else:
                    self.add_object(File(file))
        else:
            self.load_drivers()
            for driver in self.drivers:
                self.add_object(Folder(driver + ":\\", name=driver + ":\\"))

    def change_dir(self, path):
        self.pos = (self.pos[0], 0)
        if path:
            self.curr_path = path + ("" if path[-1] == "\\" else "\\")
            self.make_file_tree()
        else:
            self.curr_path = path
            self.make_file_tree()
