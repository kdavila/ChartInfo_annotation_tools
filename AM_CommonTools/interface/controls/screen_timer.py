
import time
from .screen_element import *

class ScreenTimer(ScreenElement):
    def __init__(self, name, tempo, enabled):
        ScreenElement.__init__(self, name)

        self.tempo = tempo
        self.enabled = enabled

        self.accumulated_time = 0.0
        self.last_time = time.time()
        self.timer_callback = None

    def render(self, background, off_x = 0, off_y = 0):
        # do not do anything
        if not self.enabled:
            return

        # get time delta ...
        current_time = time.time()
        delta = current_time - self.last_time

        self.accumulated_time += delta
        if self.accumulated_time >= self.tempo:
            # execute timer function ...
            if self.timer_callback is not None:
                self.timer_callback(self)
            # subtract ...
            self.accumulated_time -= self.tempo

        # store for next cycle
        self.last_time = current_time

    def stop_timer(self):
        self.enabled = False
        self.accumulated_time = 0.0
        self.last_time = None

    def start_timer(self):
        self.enabled = True
        self.accumulated_time = 0.0
        self.last_time = time.time()

