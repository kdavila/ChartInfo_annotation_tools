
import os
import cv2
import pygame
from .screen_element import *
from .screen_image import *

class ScreenHorizontalScroll(ScreenElement):
    LEFT_ARROW = cv2.imread(os.path.dirname(__file__) + "/../resources/left_arrow.bmp")
    RIGHT_ARROW = cv2.flip( LEFT_ARROW, 1 )
    
    def __init__(self, name, minimum, maximum, value, step=1):
        ScreenElement.__init__(self, name)
        
        # by default, small scroll bar
        self.width = 100
        # this should not be changed
        self.height = 16

        self.min = None
        self.max = None
        self.value = None
        self.step = None

        self.reset(minimum, maximum, value, step)

        # Left image....
        self.left_image = ScreenImage(name + "_left_arrow", ScreenHorizontalScroll.LEFT_ARROW, 16, 16, True)        
        # Right image....
        self.right_image = ScreenImage(name + "_right_arrow", ScreenHorizontalScroll.RIGHT_ARROW, 16, 16, True)        
        
        # default color and background
        self.color = (128, 128, 128)
        self.highlight = (192, 250, 128)
        self.background = (64, 64, 64)
        
        self.is_highlighted = False
        self.dragging = False
        
        self.scroll_callback = None

    def reset(self, minimum, maximum, value, step=1):
        self.min = minimum
        self.max = maximum

        # ...Validate range...
        if self.max < self.min:
            self.max = self.min + 1
        # ...Validate value...
        if self.min <= value <= self.max:
            self.value = value
        else:
            self.value = self.min

        if step <= 0:
            self.step = 1
        else:
            self.step = step

    def set_value(self, new_value):
        prev_value = self.value

        # validate ...
        if self.min <= new_value <= self.max:
            self.value = new_value

        if prev_value != self.value and self.scroll_callback is not None:
            self.scroll_callback(self)
        
    def render(self, background, off_x = 0, off_y = 0):
                        
        #render left arrow...
        self.left_image.render( background, self.position[0] + off_x, self.position[1] + off_y )
        #render right arrow..        
        self.right_image.render( background, self.position[0] + self.width - 16 + off_x, self.position[1] + off_y )
        
        #background color....
        back_x = self.position[0] + 16 + off_x
        back_y = self.position[1] + off_y
        rect = self.clip_rectangle(back_x, back_y, self.width - 32, self.height, 0, 0)
        background.fill(self.background, rect )
        
        #now the position...
        #first, estimate relative width based on step size
        scroll_range = float(self.max - self.min)
        scroll_width = int( ((self.step)/ scroll_range) * (self.width - 32) )
        if scroll_width >= self.width - 32:
            scroll_width = self.width - 33
        
        #and position according to current value...
        scroll_pos = int(  ((self.value - self.min) / scroll_range ) * (self.width - 32 - scroll_width) )
        
        scroll_x = self.position[0] + 16 + scroll_pos + off_x
        scroll_y = self.position[1] + 1 + off_y
        scroll_rect = self.clip_rectangle(scroll_x, scroll_y, scroll_width, 14, 0, 0)
        
        #...finally, draw it!...
        if self.is_highlighted:
            background.fill(self.highlight, scroll_rect )
        else:
            background.fill(self.color, scroll_rect ) 
                
        
    def on_mouse_enter(self, pos, rel, buttons):
        self.is_highlighted = True
        if buttons[0] == 1:
            self.dragging = True
            self.adjust_scroller(pos)
            
    
    def on_mouse_leave(self, pos, rel, buttons):
        self.is_highlighted = False
        self.dragging = False
        
    def on_mouse_button_click(self, pos, button):
        #check if clicked on the buttons...
        if button == 1:            
            current_val = self.value
            #just validate horizontal axis, as button covers all vertical direction
            #...left....
            if self.position[0] <= pos[0] and pos[0] <= self.position[0] + 16:
                #apply step to value...
                self.apply_step(-1)
            #...right...
            if self.position[0] + self.width - 16 <= pos[0] and pos[0] <= self.position[0] + self.width:
                #apply step to value...
                self.apply_step(1)
                    
            if self.value != current_val and self.scroll_callback != None:
                self.scroll_callback(self)
                
    def apply_step(self, sign):
        self.value += self.step * sign
        
        if self.value > self.max:
            self.value = self.max
            
        if self.value < self.min:
            self.value = self.min
                

    def on_mouse_button_down(self, pos, button):
        if button == 1:
            #check range...
            if self.position[0] + 16 < pos[0] and pos[0] < self.position[0] + self.width - 16:
                self.dragging = True
                self.adjust_scroller(pos)
                
    
    def on_mouse_motion(self, pos, rel, buttons):        
        if self.dragging:                    
            if pos[0] <= self.position[0] + 16:
                #dragged to the left
                self.value = self.min
            elif pos[0] < self.position[0] + self.width - 16:
                self.adjust_scroller(pos)
            else:
                #dragged to the right
                self.value = self.max

    def on_mouse_button_up(self, pos, button):
        if button == 1:
            self.dragging = False
            
    def adjust_scroller(self, pos):
        #get relative position
        scroll_range = float(self.max - self.min)
        scroll_width = int( ((self.step)/ scroll_range) * (self.width - 32) )
    
        relative_pos = (pos[0] - self.position[0] - 16 - scroll_width / 2)
        relative_range = float(self.width - 32 - scroll_width)
        relative_val = int((relative_pos / relative_range) * scroll_range) + self.min
        
        if relative_val < self.min:
            relative_val = self.min
        if relative_val > self.max:
            relative_val = self.max
        
        if self.value != relative_val:    
            self.value = relative_val
            if self.scroll_callback != None:
                self.scroll_callback(self)
        