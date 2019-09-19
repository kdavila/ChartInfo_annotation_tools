import pygame
from .screen_element import *
from .screen_label import *

class ScreenButton(ScreenElement):
    def __init__(self, name, text, text_size, width, height=0, text_color=None, back_color=None, centered=1):
        ScreenElement.__init__(self, name)
        
        self.padding = (10, 15, 10, 15)
        self.text_size = text_size
        self.width = width
        self.height = height
        self.original_height = height
        self.centered = centered
        
        # check colors....
        # ...text...
        if text_color is None:
            self.text_color = (0, 0, 0)
        else:
            self.text_color = text_color
        # ... background...
        if back_color is None:
            self.back_color = (255, 255, 255)
        else:
            self.back_color = back_color
        
        self.is_highlighted = False
        
        # create an inner label
        self.updateText( text )
        
        # for events...
        self.click_callback = None
        
    def setPadding(self, top, right, bottom, left):
        self.padding = (top, right, bottom, left)
        
        self.updateText(self.text)
        
    def set_colors(self, text_color, back_color ):
        self.text_color = text_color
        self.back_color = back_color
            
        self.updateText( self.text )
    
    
    def updateText(self, new_text):
        self.text = new_text
        
        #calculate max inner width for text...
        # width - padding_right - padding_left
        max_inner_width = self.width - (self.padding[1] + self.padding[3]) 
        
        #now, create an inner label
        self.inner_label = ScreenLabel(self.name + "__LABEL__", self.text, self.text_size, max_inner_width, self.centered)
        self.inner_label.position = (self.padding[3], self.padding[0])
        self.inner_label.set_color( self.text_color )
        self.inner_label.set_background( self.back_color )
        
        self.height = self.original_height
        min_height = self.padding[0] + self.padding[2] + self.inner_label.height
        if min_height > self.height:
            self.height = min_height
            
        #now, the label should be rendered on the background...
        self.rendered = pygame.Surface( (self.width, self.height ) )
        #self.rendered = self.rendered.convert()
        self.rendered.fill( self.back_color )
        
        #create the normal view...
        self.inner_label.render( self.rendered )
        
        #now, create the highlighted view...
        self.inner_label.set_color( self.back_color )
        self.inner_label.set_background( self.text_color )
        
        self.highlighted = pygame.Surface( (self.width, self.height ) )
        self.highlighted.fill( self.text_color )
        
        #render highlighted
        self.inner_label.render( self.highlighted )
        
            
    def render(self, background, off_x = 0, off_y = 0):
        #test with text...
        if not self.is_highlighted:
            background.blit( self.rendered, (self.position[0] + off_x, self.position[1] + off_y ) )
        else:
            background.blit( self.highlighted, (self.position[0] + off_x, self.position[1] + off_y ) )
        
    def on_mouse_motion(self, pos, rel, buttons):
        pass
    
    def on_mouse_enter(self, pos, rel, buttons):
        self.is_highlighted = True
    
    def on_mouse_leave(self, pos, rel, buttons):
        self.is_highlighted = False
        
    def on_mouse_button_click(self, pos, button):
        # only consider click with left button
        if button == 1 and self.click_callback != None:
            self.click_callback(self)
            
