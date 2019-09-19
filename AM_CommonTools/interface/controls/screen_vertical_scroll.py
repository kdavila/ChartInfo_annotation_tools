
import os
import cv2
import pygame
import math


from .screen_element import *
from .screen_image import *

def rotateImage(image, angle):
    #....the center of the image....
    image_center = ( image.shape[0] / 2, image.shape[1] / 2 )
    
    #...get a rotation matrix with the given angle,
    #...and rotating around image center....
    rotation_mat = cv2.getRotationMatrix2D(image_center,angle,1.0)
    #...do transformation....
    result = cv2.warpAffine(image, rotation_mat, (image.shape[0], image.shape[1]), flags=cv2.INTER_LINEAR )
    
    return result


class ScreenVerticalScroll(ScreenElement):
    LEFT_ARROW = cv2.imread(os.path.dirname(__file__) + "/../resources/left_arrow.bmp")
    UP_ARROW = rotateImage( LEFT_ARROW, -90 )
    DOWN_ARROW = cv2.flip( UP_ARROW, 0 )
            
    def __init__(self, name, minimum, maximum, value, step = 1):
        ScreenElement.__init__(self, name)
        
        #this should not be changed        
        self.width = 16
        #by default, small scroll bar
        self.height = 100
        
        self.min = minimum
        self.max = maximum
        #...Validate range...
        if self.max < self.min:
            self.max = self.min + 1
        #...Validate value...
        if self.min <= value and value <= self.max:
            self.value = value
        else:
            self.value = self.min
            
        if step <= 0:
            self.step = 1
        else:
            self.step = step
            
        #Top image...
        self.up_image = ScreenImage(name + "_up_arrow", ScreenVerticalScroll.UP_ARROW, 16, 16, True)
        #Bottom image....
        self.down_image = ScreenImage(name + "_down_arrow", ScreenVerticalScroll.DOWN_ARROW, 16, 16, True)
        
        #default color and background
        self.color = (128, 128, 128)
        self.highlight = (192, 250, 128)
        self.background = (64, 64, 64)
        
        self.is_highlighted = False
        self.dragging = False
        
        self.scroll_callback = None
            
    
    def render(self, background, off_x = 0, off_y = 0):
        #render up arrow...
        self.up_image.render( background, self.position[0] + off_x, self.position[1] + off_y )
        #render right arrow..
        self.down_image.render( background, self.position[0] + off_x, self.position[1] + self.height - 16 + off_y )
        
        #background color....
        back_x = self.position[0] + off_x
        back_y = self.position[1] + 16 + off_y
        rect = self.clip_rectangle(back_x, back_y, self.width, self.height - 32, 0, 0)
        background.fill(self.background, rect )
        
        #now the position...
        #...first, estimate relative height based on step size
        scroll_range = float(self.max - self.min)
        scroll_height = int( ((self.step)/ scroll_range) * (self.height - 32) )
        if scroll_height >= self.height - 32:
            scroll_height = self.height - 33
            
        #and position according to current value...
        scroll_pos = int(  ((self.value - self.min) / scroll_range ) * (self.height - 32 - scroll_height) )
        
        #the rectangle....
        scroll_x = self.position[0] + 1 + off_x
        scroll_y = self.position[1] + 16 + scroll_pos + off_y
        scroll_rect = self.clip_rectangle(scroll_x, scroll_y, 14, scroll_height, 0, 0)
        
        #...finally, draw it!...
        if self.is_highlighted:
            background.fill(self.highlight, scroll_rect )
        else:
            background.fill(self.color, scroll_rect )
            #(self.position[0] + 1 + off_x, self.position[1] + 16 + scroll_pos + off_y, 14, scroll_height ) 
        
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
            if self.position[1] <= pos[1] and pos[1] <= self.position[1] + 16:
                self.apply_step(-1)
            #...right...
            if self.position[1] + self.height - 16 <= pos[1] and pos[1] <= self.position[1] + self.height:
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
            if self.position[1] + 16 < pos[1] and pos[1] < self.position[1] + self.height - 16:
                self.dragging = True
                self.adjust_scroller(pos)
                
    def on_mouse_motion(self, pos, rel, buttons):        
        if self.dragging:                    
            if pos[1] <= self.position[1] + 16:
                #dragged to the top
                self.value = self.min
            elif pos[1] < self.position[1] + self.height - 16:
                self.adjust_scroller(pos)
            else:
                #dragged to the bottom
                self.value = self.max
    
    def on_mouse_button_up(self, pos, button):
        if button == 1:
            self.dragging = False
            
    def adjust_scroller(self, pos):
        #get relative position
        scroll_range = float(self.max - self.min)
        scroll_height = int( ((self.step)/ scroll_range) * (self.height - 32) )
    
        relative_pos = (pos[1] - self.position[1] - 16 - scroll_height / 2)
        relative_range = float(self.height - 32 - scroll_height)
        relative_val = int((relative_pos / relative_range) * scroll_range) + self.min
        
        if relative_val < self.min:
            relative_val = self.min
        if relative_val > self.max:
            relative_val = self.max
        
        if self.value != relative_val:    
            self.value = relative_val
            if self.scroll_callback != None:
                self.scroll_callback(self)
    
