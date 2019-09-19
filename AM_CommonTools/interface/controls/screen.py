import sys
import pygame

from .screen_container import ScreenContainer
from .screen_label import *
from .screen_button import *
from .screen_textbox import *
from .screen_image import *
from .screen_horizontal_scroll import *
from .screen_vertical_scroll import *
from .screen_paginator import *


class Screen(object):
    def __init__(self, name, size):
        self.name = name
        # self.elements = []
        self.elements = ScreenContainer(name, size)
        self.size = size
        self.width = size[0]
        self.height = size[1]

        # by default...
        self.return_screen = self

    def prepare_screen(self):
        # always return to itself by default
        self.return_screen = self

    def handle_events(self, event_list):
        # handle all events...
        for event in event_list:
            if event.type == pygame.QUIT:
                # ...SPECIAL exit event....
                sys.exit(0)
                return None
            else:
                # ...Remaining events will be handled by the container...
                self.elements.handle_event(event)

        # go to the return screen (usually itself)
        return self.return_screen

    def render(self, background):
        # render all controls
        self.elements.render(background, 0, 0)
