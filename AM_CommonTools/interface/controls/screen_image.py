import sys
import numpy as np
import cv2
import pygame

from .screen_element import *

class ScreenImage(ScreenElement):
    def __init__(self, name, image, width = 0, height = 0, keep_aspect = False, interpolation=None):
        #parent's constructor
        ScreenElement.__init__(self, name)
        
        self.border_width = 0
        self.border_color = (0, 0, 0)
        
        self.click_callback = None
                
        self.set_image(image, width, height, keep_aspect, interpolation)
        
        
    def set_image(self, image, width=0, height=0, keep_aspect = False, interpolation=None):
        self.image = image
        self.original_image = image 
        #check for default size...
        forced_resize = False
        if width == 0:
            self.width = image.shape[1]
        else:
            self.width = width
            forced_resize = True
        
        if height == 0:
            self.height = image.shape[0]
        else:
            self.height = height
            forced_resize = True
            
        #resize if needed
        if forced_resize:
            if keep_aspect:
                #must keep aspect ratio...
                h_scale = self.height / float(image.shape[0])
                w_scale = self.width / float(image.shape[1])
                
                if w_scale < h_scale:
                    #use w_scale as new scale factor...
                    self.height = int(w_scale * image.shape[0])
                else:
                    #use h_scale as new scale factor...
                    self.width = int(h_scale * image.shape[1])        

            if interpolation is None:
                # by default, use Bilinear interpolation
                interpolation = cv2.INTER_LINEAR
            self.image = cv2.resize( self.image, (self.width, self.height),interpolation=interpolation)
        
        if len(self.image.shape) == 2:
            #A Grayscale image.... create a 24-bit version of the same image...
            new_img = np.zeros( (self.image.shape[0], self.image.shape[1], 3) )
            new_img[:,:, 0] = self.image #copy on R
            new_img[:,:, 1] = self.image #copy on G
            new_img[:,:, 2] = self.image #copy on B
            
            self.image = new_img
            
        #now, create the surface...
        self.image_surface = pygame.surfarray.make_surface(np.transpose( self.image, (1,0,2) ) )

    def update_image_region(self, new_region, region_pos):
        if not isinstance(new_region, pygame.Surface):
            new_region = pygame.surfarray.make_surface(np.transpose(new_region, (1,0,2)))

        # update a portion of the image
        self.image_surface.blit(new_region, region_pos)

    def render(self, background, off_x = 0, off_y = 0):
        if self.border_width > 0:
            half = int(self.border_width / 2)
            rect = (self.position[0] - half + off_x, self.position[1] - half + off_y, self.width + half * 2, self.height + half * 2)
            pygame.draw.rect( background, self.border_color, rect, self.border_width)            
        
        background.blit(self.image_surface, (self.position[0] + off_x, self.position[1] + off_y) )
        
    def on_mouse_button_click(self, pos, button):
        #by default, do nothing
        if button == 1 and self.click_callback != None:
            self.click_callback(self)
            

        